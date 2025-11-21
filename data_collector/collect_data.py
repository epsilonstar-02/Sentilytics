import json
import os
import glob
import time
import random
import re
import logging
from datetime import datetime, timedelta
from pathlib import Path
import yt_dlp
from yt_dlp.utils import DownloadError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

PRODUCTS = [
    {
        "name": "iPhone 17",
        "release_date": "2025-09-19",
        "end_date": (datetime.strptime("2025-09-19", "%Y-%m-%d") + timedelta(days=60)).strftime("%Y-%m-%d"),
        "model_id": "A3258"  # US/PR, other regions may vary (A3519, A3520, A3521)
    },
    {
        "name": "iPhone 17 Pro",
        "release_date": "2025-09-19",
        "end_date": (datetime.strptime("2025-09-19", "%Y-%m-%d") + timedelta(days=60)).strftime("%Y-%m-%d"),
        "model_id": "A3256"  # US/PR, other regions may vary (A3522, A3523, A3524)
    },
    {
        "name": "iPhone Air",
        "release_date": "2025-09-19",
        "end_date": (datetime.strptime("2025-09-19", "%Y-%m-%d") + timedelta(days=60)).strftime("%Y-%m-%d"),
        "model_id": "A3260"  # US/PR/Bahrain/Canada/Guam/Kuwait/Mexico/Oman/Qatar/Saudi Arabia/UAE, other regions may vary (A3516, A3517, A3518)
    },
    {
        "name": "Apple Watch Series 11",
        "release_date": "2025-09-19",
        "end_date": (datetime.strptime("2025-09-19", "%Y-%m-%d") + timedelta(days=60)).strftime("%Y-%m-%d"),
        "model_id": "A3335"  # 42mm GPS+Cellular (US/EU/AP), other variants: A3337 (46mm), A3452 (China 42mm), A3453 (China 46mm)
    },
    {
        "name": "Apple Watch Ultra 3",
        "release_date": "2025-09-19",
        "end_date": (datetime.strptime("2025-09-19", "%Y-%m-%d") + timedelta(days=60)).strftime("%Y-%m-%d"),
        "model_id": "A3339"  # 49mm Titanium (US/EU/AP), other variants may exist for China
    },
    {
        "name": "AirPods Pro 3",
        "release_date": "2025-09-19",
        "end_date": (datetime.strptime("2025-09-19", "%Y-%m-%d") + timedelta(days=60)).strftime("%Y-%m-%d"),
        "model_id": "A3063"  # Standard model, other variants: A3064, A3065
    },
    {
        "name": "Apple Vision Pro M5",
        "release_date": "2025-09-19",
        "end_date": (datetime.strptime("2025-09-19", "%Y-%m-%d") + timedelta(days=60)).strftime("%Y-%m-%d"),
        "model_id": "A3416"  # M5 model, also listed as RealityDevice17,1
    },
    {
        "name": "iPad Pro M5",
        "release_date": "2025-10-22",
        "end_date": (datetime.strptime("2025-10-22", "%Y-%m-%d") + timedelta(days=60)).strftime("%Y-%m-%d"),
        "model_id": "MDWM4HN/A"  # 11-inch Wi-Fi, other variants exist for 13-inch and cellular models
    }
]


def detect_rate_limited_error(msg: str) -> bool:
    if not msg:
        return False
    m = msg.lower()
    return ('rate-limited' in m or 'try again later' in m) and 'youtube' in m

def get_video_ids(query, num_results=100):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'noplaylist': True,
    }
    
    search_query = f"ytsearch{num_results}:{query}"
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(search_query, download=False)
            if 'entries' in result:
                return result['entries']
            return []
        except Exception as e:
            logging.error(f"Error searching for {query}: {e}")
            return []

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
    output_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(output_dir, exist_ok=True)

    for product in PRODUCTS:
        logging.info(f"Processing {product['name']}...")
        
        # Setup output file and load existing progress
        filename = f"{product['name'].replace(' ', '_')}_transcripts.json"
        filepath = os.path.join(output_dir, filename)
        
        collected_data = []
        existing_video_ids = set()
        
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    collected_data = json.load(f)
                    existing_video_ids = {item['video_id'] for item in collected_data}
                logging.info(f"Resuming {product['name']}: Found {len(collected_data)} existing transcripts.")
            except json.JSONDecodeError:
                logging.warning(f"Could not decode existing file {filepath}. Starting fresh.")
        
        count = len(collected_data)
        if count >= 100:
            logging.info(f"Already have {count} transcripts for {product['name']}. Skipping.")
            continue

        # Construct query with date filters
        query = f"{product['name']} review after:{product['release_date']} before:{product['end_date']}"
        
        logging.info(f"Searching with query: {query}")
        videos = get_video_ids(query, num_results=150) # Fetch a bit more to account for duplicates/failures
        
        logging.info(f"Found {len(videos)} potential videos. Fetching transcripts...")

        for video in videos:
            if count >= 100:
                logging.info(f"Reached target of 100 transcripts for {product['name']}.")
                break
                
            video_id = video.get('id')
            title = video.get('title')
            
            if not video_id:
                continue
                
            if video_id in existing_video_ids:
                continue
            
            # Add delay to avoid rate limiting
            sleep_time = random.uniform(2, 5)
            time.sleep(sleep_time)
                
            transcript = get_transcript(video_id)
            
            if transcript:
                entry = {
                    "product": product['name'],
                    "video_id": video_id,
                    "title": title,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "transcript": transcript
                }
                collected_data.append(entry)
                existing_video_ids.add(video_id)
                count += 1
                
                # Incremental save
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(collected_data, f, indent=4, ensure_ascii=False)
                    logging.info(f"[{count}/100] Saved transcript for: {title[:50]}...")
                except Exception as e:
                    logging.error(f"Failed to save progress: {e}")
            else:
                pass
        
        logging.info(f"Finished {product['name']}. Total transcripts: {len(collected_data)}\n")

if __name__ == "__main__":
    main()
