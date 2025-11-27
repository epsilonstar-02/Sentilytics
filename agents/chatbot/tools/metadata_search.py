import os
import sys
import json
import glob
from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache
from collections import defaultdict
import statistics
import logging

from agents.chatbot.tools.constants import normalize_product_name

# Add database directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from database.db_config import get_db_session
from sqlalchemy import text

logger = logging.getLogger(__name__)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data_collector/data/metadata"))

@lru_cache(maxsize=10)
def load_metadata(product: str = None) -> List[Dict[str, Any]]:
    """
    Loads metadata for a specific product or all products from PostgreSQL.
    Cached for performance. Returns data in the same format as JSON version.
    """
    try:
        with get_db_session() as session:
            if product:
                normalized = normalize_product_name(product)
                query = text("""
                    SELECT 
                        v.video_id,
                        v.title,
                        v.description,
                        v.url,
                        v.published_at,
                        v.date,
                        v.view_count,
                        v.like_count,
                        v.comment_count,
                        v.duration,
                        v.thumbnail_url,
                        p.name as product_name,
                        c.channel_id,
                        c.channel_title
                    FROM videos v
                    JOIN products p ON v.product_id = p.id
                    LEFT JOIN channels c ON v.channel_id = c.channel_id
                    WHERE p.name = :product_name
                    ORDER BY v.published_at DESC
                """)
                result = session.execute(query, {"product_name": product})
            else:
                query = text("""
                    SELECT 
                        v.video_id,
                        v.title,
                        v.description,
                        v.url,
                        v.published_at,
                        v.date,
                        v.view_count,
                        v.like_count,
                        v.comment_count,
                        v.duration,
                        v.thumbnail_url,
                        p.name as product_name,
                        c.channel_id,
                        c.channel_title
                    FROM videos v
                    JOIN products p ON v.product_id = p.id
                    LEFT JOIN channels c ON v.channel_id = c.channel_id
                    ORDER BY v.published_at DESC
                """)
                result = session.execute(query)
            
            # Convert to old format for compatibility
            all_data = []
            for row in result:
                all_data.append({
                    'video_id': row.video_id,
                    'product': row.product_name,
                    'date': str(row.date) if row.date else None,
                    'details': {
                        'snippet': {
                            'title': row.title,
                            'description': row.description or '',
                            'publishedAt': row.published_at.isoformat() if row.published_at else None,
                            'channelId': row.channel_id,
                            'channelTitle': row.channel_title,
                            'thumbnails': {
                                'high': {'url': row.thumbnail_url}
                            }
                        },
                        'statistics': {
                            'viewCount': str(row.view_count),
                            'likeCount': str(row.like_count),
                            'commentCount': str(row.comment_count)
                        },
                        'contentDetails': {
                            'duration': row.duration
                        }
                    }
                })
            
            logger.info(f"Loaded {len(all_data)} videos from database for product: {product or 'all'}")
            return all_data
            
    except Exception as e:
        logger.error(f"Error loading metadata from database: {e}")
        return []


def search_metadata(query: str, product: str = None) -> List[Dict[str, Any]]:
    """
    Searches metadata for videos matching the query in title or description.
    Uses PostgreSQL full-text search for better performance.
    """
    try:
        with get_db_session() as session:
            sql = """
                SELECT 
                    v.video_id,
                    v.title,
                    v.description,
                    v.url,
                    v.published_at,
                    v.date,
                    v.view_count,
                    v.like_count,
                    v.comment_count,
                    p.name as product_name,
                    c.channel_title,
                    c.channel_id,
                    ts_rank(to_tsvector('english', v.title || ' ' || COALESCE(v.description, '')), 
                            to_tsquery('english', :search_query)) as rank
                FROM videos v
                JOIN products p ON v.product_id = p.id
                LEFT JOIN channels c ON v.channel_id = c.channel_id
                WHERE to_tsvector('english', v.title || ' ' || COALESCE(v.description, '')) 
                      @@ to_tsquery('english', :search_query)
            """
            
            params = {"search_query": query.replace(' ', ' & ')}
            
            if product:
                sql += " AND p.name = :product_name"
                params["product_name"] = product
            
            sql += " ORDER BY rank DESC, v.view_count DESC LIMIT 100"
            
            result = session.execute(text(sql), params)
            
            # Convert to old format
            results = []
            for row in result:
                results.append({
                    'video_id': row.video_id,
                    'product': row.product_name,
                    'date': str(row.date) if row.date else None,
                    'details': {
                        'snippet': {
                            'title': row.title,
                            'description': row.description or '',
                            'publishedAt': row.published_at.isoformat() if row.published_at else None,
                            'channelTitle': row.channel_title,
                            'channelId': row.channel_id
                        },
                        'statistics': {
                            'viewCount': str(row.view_count),
                            'likeCount': str(row.like_count),
                            'commentCount': str(row.comment_count)
                        }
                    }
                })
            
            logger.info(f"Found {len(results)} videos matching '{query}'")
            return results
            
    except Exception as e:
        logger.error(f"Error searching metadata: {e}")
        return []



def get_top_videos(product: str, metric: str = 'viewCount', limit: int = 5) -> List[Dict[str, Any]]:
    """
    Returns top videos for a product based on a metric (viewCount, likeCount).
    Uses database ORDER BY for efficiency.
    """
    try:
        metric_column = 'view_count' if metric == 'viewCount' else 'like_count'
        
        with get_db_session() as session:
            query = text(f"""
                SELECT 
                    v.video_id,
                    v.title,
                    v.description,
                    v.url,
                    v.published_at,
                    v.date,
                    v.view_count,
                    v.like_count,
                    v.comment_count,
                    v.duration,
                    v.thumbnail_url,
                    p.name as product_name,
                    c.channel_title,
                    c.channel_id
                FROM videos v
                JOIN products p ON v.product_id = p.id
                LEFT JOIN channels c ON v.channel_id = c.channel_id
                WHERE p.name = :product_name
                ORDER BY v.{metric_column} DESC
                LIMIT :limit
            """)
            
            result = session.execute(query, {
                "product_name": product,
                "limit": limit
            })
            
            # Convert to old format
            sorted_data = []
            for row in result:
                sorted_data.append({
                    'video_id': row.video_id,
                    'product': row.product_name,
                    'date': str(row.date) if row.date else None,
                    'details': {
                        'snippet': {
                            'title': row.title,
                            'description': row.description or '',
                            'publishedAt': row.published_at.isoformat() if row.published_at else None,
                            'channelId': row.channel_id,
                            'channelTitle': row.channel_title,
                            'thumbnails': {
                                'high': {'url': row.thumbnail_url}
                            }
                        },
                        'statistics': {
                            'viewCount': str(row.view_count),
                            'likeCount': str(row.like_count),
                            'commentCount': str(row.comment_count)
                        },
                        'contentDetails': {
                            'duration': row.duration
                        }
                    }
                })
            
            logger.info(f"Retrieved top {len(sorted_data)} videos for {product} by {metric}")
            return sorted_data
            
    except Exception as e:
        logger.error(f"Error getting top videos: {e}")
        return []



def get_temporal_trends(product: str, metric: str = 'viewCount', days: int = 7) -> Dict[str, Any]:
    """
    Analyzes temporal trends for a product's videos over time.
    Returns daily aggregates and growth metrics.
    Uses PostgreSQL aggregation for much better performance!
    """
    try:
        metric_column = 'view_count' if metric == 'viewCount' else 'like_count'
        
        with get_db_session() as session:
            query = text(f"""
                SELECT 
                    v.date,
                    COUNT(*) as video_count,
                    SUM(v.{metric_column}) as total,
                    AVG(v.{metric_column})::INTEGER as average,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY v.{metric_column}) as median,
                    MAX(v.{metric_column}) as max_value
                FROM videos v
                JOIN products p ON v.product_id = p.id
                WHERE p.name = :product_name
                  AND v.date >= CURRENT_DATE - INTERVAL ':days days'
                GROUP BY v.date
                ORDER BY v.date
            """)
            
            result = session.execute(query, {
                "product_name": product,
                "days": days
            })
            
            daily_aggregates = {}
            for row in result:
                date_str = str(row.date)
                daily_aggregates[date_str] = {
                    'total': int(row.total or 0),
                    'average': int(row.average or 0),
                    'median': float(row.median or 0),
                    'count': int(row.video_count),
                    'max': int(row.max_value or 0)
                }
            
            # Calculate growth rate
            dates = sorted(daily_aggregates.keys())
            growth_rate = 0
            if len(dates) >= 2:
                first_total = daily_aggregates[dates[0]]['total']
                last_total = daily_aggregates[dates[-1]]['total']
                if first_total > 0:
                    growth_rate = ((last_total - first_total) / first_total) * 100
            
            return {
                'daily_data': daily_aggregates,
                'growth_rate': growth_rate,
                'period_days': days,
                'total_videos': sum(d['count'] for d in daily_aggregates.values())
            }
            
    except Exception as e:
        logger.error(f"Error getting temporal trends: {e}")
        return {'daily_data': {}, 'growth_rate': 0, 'period_days': days, 'total_videos': 0}

    
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
