import os
import json
import glob
from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache
from collections import defaultdict
import statistics

from agents.chatbot.tools.constants import normalize_product_name

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data_collector/data/metadata"))

@lru_cache(maxsize=4)
def load_metadata(product: str = None) -> List[Dict[str, Any]]:
    """Loads metadata for a specific product or all products. Cached for performance."""
    all_data = []
    
    search_path = os.path.join(DATA_DIR, "**", "*.json")
    if product:
        normalized = normalize_product_name(product)
        search_path = os.path.join(DATA_DIR, normalized, "*.json")

    files = glob.glob(search_path, recursive=True)
    
    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_data.extend(data)
                else:
                    all_data.append(data)
        except Exception as e:
            print(f"Error reading {file}: {e}")
            
    return all_data

def search_metadata(query: str, product: str = None) -> List[Dict[str, Any]]:
    """
    Searches metadata for videos matching the query in title or description.
    """
    data = load_metadata(product)
    results = []
    query_lower = query.lower()
    
    for item in data:
        details = item.get('details', {})
        snippet = details.get('snippet', {})
        title = snippet.get('title', '').lower()
        description = snippet.get('description', '').lower()
        
        if query_lower in title or query_lower in description:
            results.append(item)
            
    return results

def get_top_videos(product: str, metric: str = 'viewCount', limit: int = 5) -> List[Dict[str, Any]]:
    """
    Returns top videos for a product based on a metric (viewCount, likeCount).
    """
    data = load_metadata(product)
    
    def get_metric(item):
        try:
            return int(item.get('details', {}).get('statistics', {}).get(metric, 0))
        except:
            return 0
            
    sorted_data = sorted(data, key=get_metric, reverse=True)
    return sorted_data[:limit]

def get_temporal_trends(product: str, metric: str = 'viewCount', days: int = 7) -> Dict[str, Any]:
    """
    Analyzes temporal trends for a product's videos over time.
    Returns daily aggregates and growth metrics.
    """
    data = load_metadata(product)
    
    # Group by date
    daily_data = defaultdict(list)
    for item in data:
        date = item.get('date')
        if not date:
            continue
        try:
            value = int(item.get('details', {}).get('statistics', {}).get(metric, 0))
            daily_data[date].append(value)
        except:
            continue
    
    # Calculate daily aggregates
    daily_aggregates = {}
    for date, values in sorted(daily_data.items()):
        daily_aggregates[date] = {
            'total': sum(values),
            'average': statistics.mean(values) if values else 0,
            'median': statistics.median(values) if values else 0,
            'count': len(values),
            'max': max(values) if values else 0
        }
    
    # Calculate growth trends
    dates = sorted(daily_aggregates.keys())
    if len(dates) >= 2:
        recent_avg = statistics.mean([daily_aggregates[d]['average'] for d in dates[-days:]])
        older_avg = statistics.mean([daily_aggregates[d]['average'] for d in dates[:days]])
        growth_rate = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
    else:
        growth_rate = 0
    
    return {
        'product': product,
        'metric': metric,
        'daily_aggregates': daily_aggregates,
        'growth_rate_percent': round(growth_rate, 2),
        'total_videos': sum(d['count'] for d in daily_aggregates.values())
    }

def get_channel_insights(product: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Analyzes channel-level performance for a product.
    Identifies top creators and their engagement metrics.
    """
    data = load_metadata(product)
    
    # Group by channel
    channel_data = defaultdict(lambda: {'videos': [], 'total_views': 0, 'total_likes': 0})
    
    for item in data:
        details = item.get('details', {})
        snippet = details.get('snippet', {})
        stats = details.get('statistics', {})
        
        channel_id = snippet.get('channelId')
        channel_title = snippet.get('channelTitle')
        
        if not channel_id:
            continue
            
        try:
            views = int(stats.get('viewCount', 0))
            likes = int(stats.get('likeCount', 0))
            
            channel_data[channel_id]['channel_title'] = channel_title
            channel_data[channel_id]['channel_id'] = channel_id
            channel_data[channel_id]['videos'].append(item)
            channel_data[channel_id]['total_views'] += views
            channel_data[channel_id]['total_likes'] += likes
        except:
            continue
    
    # Calculate metrics per channel
    channel_list = []
    for channel_id, info in channel_data.items():
        video_count = len(info['videos'])
        channel_list.append({
            'channel_id': channel_id,
            'channel_title': info.get('channel_title', 'Unknown'),
            'video_count': video_count,
            'total_views': info['total_views'],
            'total_likes': info['total_likes'],
            'avg_views_per_video': info['total_views'] / video_count if video_count > 0 else 0,
            'engagement_rate': (info['total_likes'] / info['total_views'] * 100) if info['total_views'] > 0 else 0
        })
    
    # Sort by total views
    channel_list.sort(key=lambda x: x['total_views'], reverse=True)
    return channel_list[:limit]

def compare_products(product_list: List[str], metric: str = 'viewCount') -> Dict[str, Any]:
    """
    Compares multiple products across specified metrics.
    """
    comparison = {}
    
    for product in product_list:
        data = load_metadata(product)
        
        if not data:
            comparison[product] = {'error': 'No data found'}
            continue
        
        # Calculate aggregate metrics
        values = []
        for item in data:
            try:
                value = int(item.get('details', {}).get('statistics', {}).get(metric, 0))
                values.append(value)
            except:
                continue
        
        if values:
            comparison[product] = {
                'video_count': len(data),
                'total': sum(values),
                'average': statistics.mean(values),
                'median': statistics.median(values),
                'max': max(values),
                'min': min(values),
                'std_dev': statistics.stdev(values) if len(values) > 1 else 0
            }
        else:
            comparison[product] = {'error': 'No valid data'}
    
    return {
        'metric': metric,
        'products': comparison
    }

def get_engagement_metrics(product: str) -> Dict[str, Any]:
    """
    Calculates comprehensive engagement metrics for a product.
    """
    data = load_metadata(product)
    
    total_views = 0
    total_likes = 0
    total_comments = 0
    engagement_scores = []
    
    for item in data:
        stats = item.get('details', {}).get('statistics', {})
        try:
            views = int(stats.get('viewCount', 0))
            likes = int(stats.get('likeCount', 0))
            comments = int(stats.get('commentCount', 0))
            
            total_views += views
            total_likes += likes
            total_comments += comments
            
            # Engagement score: (likes + comments) / views * 100
            if views > 0:
                engagement_scores.append((likes + comments) / views * 100)
        except:
            continue
    
    return {
        'product': product,
        'total_videos': len(data),
        'total_views': total_views,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'avg_engagement_rate': statistics.mean(engagement_scores) if engagement_scores else 0,
        'like_to_view_ratio': (total_likes / total_views * 100) if total_views > 0 else 0,
        'comment_to_view_ratio': (total_comments / total_views * 100) if total_views > 0 else 0
    }
