import json
import os
import time
import random
import re
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import yt_dlp
from yt_dlp.utils import DownloadError
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_logging(verbose=False):
    """Configure logging with optional verbose mode for detailed transcript download info."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

if not YOUTUBE_API_KEY:
    logging.warning("YOUTUBE_API_KEY not found in environment variables. API calls will fail.")

PRODUCTS = [
    {"name": "ChatGPT GPT-5"},
    {"name": "MacBook Pro 14-inch M5"}
]


def detect_rate_limited_error(msg: str) -> bool:
    if not msg:
        return False
    m = msg.lower()
    return ('rate-limited' in m or 'try again later' in m) and 'youtube' in m

def get_youtube_service():
    return build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def search_videos_api(service, query, published_after, published_before, max_results=100):
    video_ids = []
    next_page_token = None
    
    # Convert dates to RFC 3339 format
    # published_after is "YYYY-MM-DD", we need "YYYY-MM-DDT00:00:00Z"
    published_after_rfc = f"{published_after}T00:00:00Z"
    published_before_rfc = f"{published_before}T00:00:00Z"

    while len(video_ids) < max_results:
        try:
            request = service.search().list(
                part="id",
                q=query,
                type="video",
                publishedAfter=published_after_rfc,
                publishedBefore=published_before_rfc,
                maxResults=min(50, max_results - len(video_ids)),
                pageToken=next_page_token,
                order="relevance"
            )
            response = request.execute()
            
            for item in response.get('items', []):
                video_ids.append(item['id']['videoId'])
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
                
        except Exception as e:
            logging.error(f"Error searching YouTube API: {e}")
            break
            
    return video_ids

def get_video_details_api(service, video_ids):
    details = {}
    # API allows max 50 ids per call
    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i+50]
        try:
            request = service.videos().list(
                part="snippet,statistics,contentDetails",
                id=','.join(batch_ids)
            )
            response = request.execute()
            
            for item in response.get('items', []):
                details[item['id']] = item
        except Exception as e:
            logging.error(f"Error fetching video details: {e}")
            
    return details

def get_transcript(video_id, video_title=None):
    """
    Retrieve English transcripts for a given YouTube video ID using yt-dlp.
    Returns a tuple of (transcript_text, status) where status is one of:
    - 'success': Transcript was successfully retrieved
    - 'rate_limited': YouTube rate limited the request
    - 'no_captions': Video has no captions available
    - 'download_error': yt-dlp failed to download
    - 'parse_error': Failed to parse the VTT file
    - 'empty': Transcript file was empty
    """
    video_url = f'https://www.youtube.com/watch?v={video_id}'
    display_title = f"'{video_title[:40]}...'" if video_title and len(video_title) > 40 else f"'{video_title}'" if video_title else video_id
    
    logging.debug(f"  Attempting transcript download for {display_title}")
    
    # Use a temp directory for transcripts
    script_dir = Path(__file__).resolve().parent
    transcript_output_dir = script_dir / "temp_transcripts"
    transcript_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check for cookies file in root or current dir
    cookies_file = script_dir.parent / 'cookies.txt'
    if not cookies_file.exists():
        cookies_file = script_dir / 'cookies.txt'
    
    ydl_opts = {
        'writesubtitles': True,
        'subtitleslangs': ['en'],
        'writeautomaticsub': True,
        'skip_download': True,
        'outtmpl': str(transcript_output_dir / f'{video_id}'),
        'quiet': True,
        'noprogress': True,
        'noplaylist': True,
        'ignore_no_formats_error': True,
    }

    if cookies_file.exists():
        ydl_opts['cookiefile'] = str(cookies_file)

    # Clear any stale transcript artifacts
    for stale in transcript_output_dir.glob(f'{video_id}.*.vtt'):
        try:
            stale.unlink()
        except OSError:
            pass

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except DownloadError as e:
        msg = str(e)
        if detect_rate_limited_error(msg):
            logging.warning(f"  ⚠ RATE LIMITED: {display_title} - Consider waiting before retrying")
            return None, 'rate_limited'
        logging.debug(f"  ✗ Download error for {display_title}: {msg[:100]}")
        return None, 'download_error'
    except Exception as e:
        logging.debug(f"  ✗ Unexpected error for {display_title}: {e}")
        return None, 'download_error'

    # Find the downloaded VTT file
    transcript_file = next(transcript_output_dir.glob(f'{video_id}.*.vtt'), None)
    
    if not transcript_file:
        logging.debug(f"  ✗ No captions available for {display_title}")
        return None, 'no_captions'

    # Parse VTT
    try:
        with open(transcript_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.splitlines()
        text_lines = []
        seen_lines = set()
        
        for line in lines:
            if '-->' in line:
                continue
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.isdigit():
                continue
            if stripped.startswith('WEBVTT') or stripped.startswith('Kind:') or stripped.startswith('Language:'):
                continue
            
            # Remove HTML tags
            clean_line = re.sub(r'<[^>]+>', '', stripped)
            
            # Avoid duplicates (common in VTT)
            if clean_line not in seen_lines:
                text_lines.append(clean_line)
                seen_lines.add(clean_line)
        
        # Cleanup
        transcript_file.unlink()
        
        if not text_lines:
            logging.debug(f"  ✗ Empty transcript for {display_title}")
            return None, 'empty'
        
        transcript_text = " ".join(text_lines).replace('\n', ' ').replace('\r', ' ')
        word_count = len(transcript_text.split())
        logging.debug(f"  ✓ Got transcript for {display_title} ({word_count} words)")
        return transcript_text, 'success'
        
    except Exception as e:
        logging.error(f"  ✗ Parse error for {display_title}: {e}")
        return None, 'parse_error'


def find_latest_collected_date(transcripts_dir):
    """
    Find the latest date that has data collected across all products.
    Returns the day after the latest date found, so we resume from new data.
    """
    latest_date = None
    
    for product in PRODUCTS:
        product_safe_name = product['name'].replace(' ', '_')
        prod_trans_dir = os.path.join(transcripts_dir, product_safe_name)
        
        if not os.path.exists(prod_trans_dir):
            continue
            
        for filename in os.listdir(prod_trans_dir):
            if filename.endswith('.json'):
                date_str = filename.replace('.json', '')
                try:
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if latest_date is None or file_date > latest_date:
                        latest_date = file_date
                except ValueError:
                    continue
    
    return latest_date


def main():
    service = get_youtube_service()
    base_dir = os.path.dirname(__file__)
    metadata_dir = os.path.join(base_dir, "data", "metadata")
    transcripts_dir = os.path.join(base_dir, "data", "transcripts")
    
    os.makedirs(metadata_dir, exist_ok=True)
    os.makedirs(transcripts_dir, exist_ok=True)

    # Define the date range for data collection
    original_start_date = datetime(2025, 10, 23)
    end_date = datetime(2025, 11, 15)
    
    # Check for --resume flag to skip already collected dates
    args = parse_args()
    if args.resume:
        latest_date = find_latest_collected_date(transcripts_dir)
        if latest_date:
            # Start from the day after the latest collected date
            start_date = latest_date + timedelta(days=1)
            logging.info(f"Resuming from {start_date.strftime('%Y-%m-%d')} (latest data: {latest_date.strftime('%Y-%m-%d')})")
        else:
            start_date = original_start_date
            logging.info("No existing data found, starting from beginning.")
    else:
        start_date = original_start_date
    
    if start_date > end_date:
        logging.info("All dates already collected. Nothing to do.")
        return
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        next_date = current_date + timedelta(days=1)
        next_date_str = next_date.strftime("%Y-%m-%d")
        
        logging.info(f"=== Processing Date: {date_str} ===")

        for product in PRODUCTS:
            product_name = product['name']
            product_safe_name = product_name.replace(' ', '_')
            
            # Create product-specific directories
            prod_meta_dir = os.path.join(metadata_dir, product_safe_name)
            prod_trans_dir = os.path.join(transcripts_dir, product_safe_name)
            os.makedirs(prod_meta_dir, exist_ok=True)
            os.makedirs(prod_trans_dir, exist_ok=True)
            
            # Files for this specific day
            meta_filepath = os.path.join(prod_meta_dir, f"{date_str}.json")
            trans_filepath = os.path.join(prod_trans_dir, f"{date_str}.json")
            
            collected_transcripts = []
            collected_metadata = []
            existing_video_ids = set()
            
            # Load existing transcripts to know what we have
            if os.path.exists(trans_filepath):
                try:
                    with open(trans_filepath, 'r', encoding='utf-8') as f:
                        collected_transcripts = json.load(f)
                        existing_video_ids = {item['video_id'] for item in collected_transcripts}
                    logging.info(f"Resuming {product_name} for {date_str}: Found {len(collected_transcripts)} existing transcripts.")
                except json.JSONDecodeError:
                    logging.warning(f"Could not decode existing transcript file {trans_filepath}.")

            # Load existing metadata
            if os.path.exists(meta_filepath):
                try:
                    with open(meta_filepath, 'r', encoding='utf-8') as f:
                        collected_metadata = json.load(f)
                except json.JSONDecodeError:
                    pass
            
            count = len(collected_transcripts)
            if count >= 100:
                logging.info(f"Already have {count} transcripts for {product_name} on {date_str}. Skipping.")
                continue

            # Search via API
            query = product_name
            logging.info(f"Searching for {product_name} on {date_str} via API...")
            
            video_ids = search_videos_api(service, query, date_str, next_date_str, max_results=120)
            
            if not video_ids:
                logging.info(f"No videos found for {product_name} on {date_str}.")
                continue
                
            logging.info(f"Found {len(video_ids)} videos. Fetching details...")
            
            # Get details for all videos found
            video_details_map = get_video_details_api(service, video_ids)
            
            # Track statistics for this product/date
            stats = {
                'attempted': 0,
                'success': 0,
                'no_captions': 0,
                'rate_limited': 0,
                'download_error': 0,
                'parse_error': 0,
                'empty': 0,
                'skipped_existing': 0,
                'skipped_no_details': 0
            }

            for video_id in video_ids:
                if count >= 100:
                    logging.info(f"✓ Reached target of 100 transcripts for {product_name} on {date_str}.")
                    break
                    
                if video_id in existing_video_ids:
                    stats['skipped_existing'] += 1
                    continue
                
                details = video_details_map.get(video_id)
                if not details:
                    stats['skipped_no_details'] += 1
                    continue
                    
                title = details['snippet']['title']
                stats['attempted'] += 1
                
                # Add delay to avoid rate limiting for yt-dlp
                sleep_time = random.uniform(2, 5)
                time.sleep(sleep_time)
                
                # Progress indicator every 10 attempts
                if stats['attempted'] % 10 == 0:
                    logging.info(f"  Progress: {stats['attempted']} attempted, {stats['success']} successful...")
                    
                transcript, status = get_transcript(video_id, title)
                
                # Track the status
                if status != 'success':
                    stats[status] = stats.get(status, 0) + 1
                    
                    # If rate limited, log warning and consider stopping
                    if status == 'rate_limited':
                        logging.warning(f"  ⚠ Rate limit hit after {stats['attempted']} attempts. Consider pausing.")
                
                if transcript:
                    stats['success'] += 1
                    
                    # Save Transcript
                    trans_entry = {
                        "product": product_name,
                        "date": date_str,
                        "video_id": video_id,
                        "title": title,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "transcript": transcript
                    }
                    collected_transcripts.append(trans_entry)
                    
                    # Save Metadata
                    meta_entry = {
                        "product": product_name,
                        "date": date_str,
                        "video_id": video_id,
                        "details": details
                    }
                    collected_metadata.append(meta_entry)
                    
                    existing_video_ids.add(video_id)
                    count += 1
                    
                    # Incremental save for both
                    try:
                        with open(trans_filepath, 'w', encoding='utf-8') as f:
                            json.dump(collected_transcripts, f, indent=4, ensure_ascii=False)
                        with open(meta_filepath, 'w', encoding='utf-8') as f:
                            json.dump(collected_metadata, f, indent=4, ensure_ascii=False)
                            
                        logging.info(f"  ✓ [{count}/100] Saved: {title[:50]}...")
                    except Exception as e:
                        logging.error(f"  ✗ Failed to save progress: {e}")
            
            # Log summary statistics for this product/date
            if stats['attempted'] > 0:
                success_rate = (stats['success'] / stats['attempted']) * 100
                logging.info(f"  ── Summary for {product_name} on {date_str} ──")
                logging.info(f"     Attempted: {stats['attempted']} | Success: {stats['success']} ({success_rate:.1f}%)")
                if stats['no_captions'] > 0:
                    logging.info(f"     No captions: {stats['no_captions']}")
                if stats['rate_limited'] > 0:
                    logging.warning(f"     Rate limited: {stats['rate_limited']}")
                if stats['download_error'] > 0:
                    logging.info(f"     Download errors: {stats['download_error']}")
                if stats['skipped_existing'] > 0:
                    logging.info(f"     Skipped (already have): {stats['skipped_existing']}")
            
        current_date += timedelta(days=1)


def parse_args():
    parser = argparse.ArgumentParser(description='Collect YouTube video data and transcripts')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose logging (shows individual transcript download attempts)')
    parser.add_argument('-r', '--resume', action='store_true',
                        help='Resume from the day after the latest collected date (skip already collected dates)')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    setup_logging(verbose=args.verbose)
    main()
