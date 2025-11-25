import json
import os
import time
import random
import re
import logging
from datetime import datetime, timedelta
from pathlib import Path
import yt_dlp
from yt_dlp.utils import DownloadError
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

if not YOUTUBE_API_KEY:
    logging.warning("YOUTUBE_API_KEY not found in environment variables. API calls will fail.")

PRODUCTS = [
    {"name": "iPhone 17 Pro"},
    {"name": "ChatGPT GPT-5"},
    {"name": "MacBook Pro 14-inch M5"},
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

def get_transcript(video_id):
    """
    Retrieve English transcripts for a given YouTube video ID using yt-dlp.
    Returns the transcript as a continuous paragraph of text.
    """
    video_url = f'https://www.youtube.com/watch?v={video_id}'
    
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
        # logging.info("Found cookies.txt, using authenticated yt-dlp session.")

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
            logging.warning(f"Rate limited for {video_id}")
            return None
        # logging.error(f"yt-dlp download error for {video_id}: {msg}")
        return None
    except Exception as e:
        # logging.error(f"yt-dlp unexpected error for {video_id}: {e}")
        return None

    # Find the downloaded VTT file
    transcript_file = next(transcript_output_dir.glob(f'{video_id}.*.vtt'), None)
    
    if not transcript_file:
        return None

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
            return None
            
        return " ".join(text_lines).replace('\n', ' ').replace('\r', ' ')
        
    except Exception as e:
        logging.error(f"Error parsing transcript for {video_id}: {e}")
        return None

def main():
    service = get_youtube_service()
    base_dir = os.path.dirname(__file__)
    metadata_dir = os.path.join(base_dir, "data", "metadata")
    transcripts_dir = os.path.join(base_dir, "data", "transcripts")
    
    os.makedirs(metadata_dir, exist_ok=True)
    os.makedirs(transcripts_dir, exist_ok=True)

    # Define the date range for data collection
    # Starting from Oct 23, 2025 to Nov 23, 2025 (Current Date)
    start_date = datetime(2025, 10, 23)
    end_date = datetime(2025, 11, 23)
    
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

            for video_id in video_ids:
                if count >= 100:
                    logging.info(f"Reached target of 100 transcripts for {product_name} on {date_str}.")
                    break
                    
                if video_id in existing_video_ids:
                    continue
                
                details = video_details_map.get(video_id)
                if not details:
                    continue
                    
                title = details['snippet']['title']
                
                # Add delay to avoid rate limiting for yt-dlp
                sleep_time = random.uniform(2, 5)
                time.sleep(sleep_time)
                    
                transcript = get_transcript(video_id)
                
                if transcript:
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
                            
                        logging.info(f"[{count}/100] Saved data for {product_name} ({date_str}): {title[:30]}...")
                    except Exception as e:
                        logging.error(f"Failed to save progress: {e}")
                else:
                    pass
            
        current_date += timedelta(days=1)

if __name__ == "__main__":
    main()
