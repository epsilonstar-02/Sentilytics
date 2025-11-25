import os
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def get_channel_info(channel_id: str):
    """
    Fetches channel information (subscriber count, etc.) from YouTube API.
    """
    if not YOUTUBE_API_KEY:
        return {"error": "YOUTUBE_API_KEY not found in environment."}

    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        
        request = youtube.channels().list(
            part="statistics,snippet",
            id=channel_id
        )
        response = request.execute()
        
        if 'items' in response and len(response['items']) > 0:
            item = response['items'][0]
            stats = item['statistics']
            snippet = item['snippet']
            
            return {
                "channelId": channel_id,
                "title": snippet.get('title'),
                "subscriberCount": stats.get('subscriberCount'),
                "viewCount": stats.get('viewCount'),
                "videoCount": stats.get('videoCount')
            }
        else:
            return {"error": "Channel not found."}
            
    except Exception as e:
        return {"error": str(e)}

def get_channels_info(channel_ids: list):
    """
    Fetches info for multiple channels.
    """
    results = []
    # API allows up to 50 ids per request
    chunk_size = 50
    for i in range(0, len(channel_ids), chunk_size):
        chunk = channel_ids[i:i+chunk_size]
        ids_str = ",".join(chunk)
        
        if not YOUTUBE_API_KEY:
             return [{"error": "YOUTUBE_API_KEY not found"}]

        try:
            youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
            request = youtube.channels().list(
                part="statistics,snippet",
                id=ids_str
            )
            response = request.execute()
            
            for item in response.get('items', []):
                stats = item['statistics']
                snippet = item['snippet']
                results.append({
                    "channelId": item['id'],
                    "title": snippet.get('title'),
                    "subscriberCount": stats.get('subscriberCount'),
                    "viewCount": stats.get('viewCount'),
                    "videoCount": stats.get('videoCount')
                })
        except Exception as e:
            results.append({"error": str(e)})
            
    return results
