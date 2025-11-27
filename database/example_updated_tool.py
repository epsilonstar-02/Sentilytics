"""
Updated Metadata Search Tool - PostgreSQL Version
This is an example of how to update the existing tools to use PostgreSQL

Original file: agents/chatbot/tools/metadata_search.py
This version uses PostgreSQL instead of JSON files
"""

import sys
import os
from typing import List, Dict, Any, Optional
from functools import lru_cache
from datetime import datetime, timedelta
import logging

# Add database directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from database.db_config import get_db_session
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Product name normalization (keep for compatibility)
def normalize_product_name(product: str) -> str:
    """Normalize product names for consistency"""
    mapping = {
        "iphone 17 pro": "iPhone_17_Pro",
        "iphone17pro": "iPhone_17_Pro",
        "iphone 17": "iPhone_17_Pro",
        "macbook pro m5": "MacBook_Pro_14-inch_M5",
        "macbook m5": "MacBook_Pro_14-inch_M5",
        "macbook": "MacBook_Pro_14-inch_M5",
        "chatgpt": "ChatGPT_GPT-5",
        "gpt-5": "ChatGPT_GPT-5",
        "gpt5": "ChatGPT_GPT-5",
    }
    return mapping.get(product.lower().strip(), product)


@lru_cache(maxsize=10)
def load_metadata(product: str = None) -> List[Dict[str, Any]]:
    """
    Load video metadata from PostgreSQL database.
    Cached for performance (similar to old JSON version).
    
    Args:
        product: Product name (e.g., "iPhone 17 Pro") or None for all products
    
    Returns:
        List of video dictionaries with metadata
    """
    try:
        with get_db_session() as session:
            if product:
                # Normalize product name
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
                        p.normalized_name as product_normalized,
                        c.channel_id,
                        c.channel_title,
                        v.raw_details
                    FROM videos v
                    JOIN products p ON v.product_id = p.id
                    LEFT JOIN channels c ON v.channel_id = c.channel_id
                    WHERE p.normalized_name = :product_name
                    ORDER BY v.published_at DESC
                """)
                
                result = session.execute(query, {"product_name": normalized})
            else:
                # Load all products
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
                        p.normalized_name as product_normalized,
                        c.channel_id,
                        c.channel_title,
                        v.raw_details
                    FROM videos v
                    JOIN products p ON v.product_id = p.id
                    LEFT JOIN channels c ON v.channel_id = c.channel_id
                    ORDER BY v.published_at DESC
                """)
                
                result = session.execute(query)
            
            # Convert to list of dicts (compatible with old format)
            videos = []
            for row in result:
                videos.append({
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
            
            logger.info(f"Loaded {len(videos)} videos from database for product: {product or 'all'}")
            return videos
            
    except Exception as e:
        logger.error(f"Error loading metadata from database: {e}")
        return []


def search_metadata(query: str, product: str = None) -> List[Dict[str, Any]]:
    """
    Search videos by keyword in title or description.
    Uses PostgreSQL full-text search for better performance.
    
    Args:
        query: Search keyword
        product: Optional product filter
    
    Returns:
        List of matching videos
    """
    try:
        with get_db_session() as session:
            # Build query with optional product filter
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
                normalized = normalize_product_name(product)
                sql += " AND p.normalized_name = :product_name"
                params["product_name"] = normalized
            
            sql += " ORDER BY rank DESC, v.view_count DESC LIMIT 100"
            
            result = session.execute(text(sql), params)
            
            # Convert to old format for compatibility
            videos = []
            for row in result:
                videos.append({
                    'video_id': row.video_id,
                    'product': row.product_name,
                    'date': str(row.date) if row.date else None,
                    'details': {
                        'snippet': {
                            'title': row.title,
                            'description': row.description or '',
                            'publishedAt': row.published_at.isoformat() if row.published_at else None,
                            'channelTitle': row.channel_title
                        },
                        'statistics': {
                            'viewCount': str(row.view_count),
                            'likeCount': str(row.like_count),
                            'commentCount': str(row.comment_count)
                        }
                    }
                })
            
            logger.info(f"Found {len(videos)} videos matching '{query}'")
            return videos
            
    except Exception as e:
        logger.error(f"Error searching metadata: {e}")
        return []


def get_top_videos(product: str, metric: str = 'viewCount', limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get top videos for a product by metric (views or likes).
    Uses database ORDER BY for efficiency.
    
    Args:
        product: Product name
        metric: 'viewCount' or 'likeCount'
        limit: Number of results
    
    Returns:
        List of top videos
    """
    try:
        normalized = normalize_product_name(product)
        
        # Map metric names
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
                    p.name as product_name,
                    c.channel_title,
                    c.channel_id
                FROM videos v
                JOIN products p ON v.product_id = p.id
                LEFT JOIN channels c ON v.channel_id = c.channel_id
                WHERE p.normalized_name = :product_name
                ORDER BY v.{metric_column} DESC
                LIMIT :limit
            """)
            
            result = session.execute(query, {
                "product_name": normalized,
                "limit": limit
            })
            
            # Convert to old format
            videos = []
            for row in result:
                videos.append({
                    'video_id': row.video_id,
                    'product': row.product_name,
                    'date': str(row.date) if row.date else None,
                    'details': {
                        'snippet': {
                            'title': row.title,
                            'description': row.description or '',
                            'publishedAt': row.published_at.isoformat() if row.published_at else None,
                            'channelId': row.channel_id,
                            'channelTitle': row.channel_title
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
            
            logger.info(f"Retrieved top {len(videos)} videos for {product} by {metric}")
            return videos
            
    except Exception as e:
        logger.error(f"Error getting top videos: {e}")
        return []


def get_temporal_trends(product: str, metric: str = 'viewCount', days: int = 7) -> Dict[str, Any]:
    """
    Analyze temporal trends using PostgreSQL aggregation.
    Much faster than loading all JSON files!
    
    Args:
        product: Product name
        metric: 'viewCount' or 'likeCount'
        days: Number of days to analyze
    
    Returns:
        Dictionary with daily aggregates and trends
    """
    try:
        normalized = normalize_product_name(product)
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
                WHERE p.normalized_name = :product_name
                  AND v.date >= CURRENT_DATE - INTERVAL ':days days'
                GROUP BY v.date
                ORDER BY v.date
            """)
            
            result = session.execute(query, {
                "product_name": normalized,
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
            if len(dates) >= 2:
                first_total = daily_aggregates[dates[0]]['total']
                last_total = daily_aggregates[dates[-1]]['total']
                growth_rate = ((last_total - first_total) / first_total * 100) if first_total > 0 else 0
            else:
                growth_rate = 0
            
            return {
                'daily_data': daily_aggregates,
                'growth_rate': growth_rate,
                'period_days': days,
                'total_videos': sum(d['count'] for d in daily_aggregates.values())
            }
            
    except Exception as e:
        logger.error(f"Error getting temporal trends: {e}")
        return {'daily_data': {}, 'growth_rate': 0, 'period_days': days, 'total_videos': 0}


# Additional helper functions for database queries

def get_video_by_id(video_id: str) -> Optional[Dict[str, Any]]:
    """Get a single video by ID"""
    try:
        with get_db_session() as session:
            query = text("""
                SELECT * FROM video_details WHERE video_id = :video_id
            """)
            result = session.execute(query, {"video_id": video_id})
            row = result.fetchone()
            
            if row:
                return dict(row._mapping)
            return None
    except Exception as e:
        logger.error(f"Error getting video by ID: {e}")
        return None


def get_videos_by_date_range(product: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Get videos within a date range"""
    try:
        normalized = normalize_product_name(product)
        
        with get_db_session() as session:
            query = text("""
                SELECT * FROM video_details
                WHERE product_normalized_name = :product_name
                  AND date BETWEEN :start_date AND :end_date
                ORDER BY date, view_count DESC
            """)
            
            result = session.execute(query, {
                "product_name": normalized,
                "start_date": start_date,
                "end_date": end_date
            })
            
            return [dict(row._mapping) for row in result]
    except Exception as e:
        logger.error(f"Error getting videos by date range: {e}")
        return []


# Keep old function names for backward compatibility
__all__ = [
    'load_metadata',
    'search_metadata',
    'get_top_videos',
    'get_temporal_trends',
    'normalize_product_name',
    'get_video_by_id',
    'get_videos_by_date_range'
]


if __name__ == "__main__":
    """Test the updated functions"""
    print("Testing PostgreSQL Metadata Search...")
    
    # Test 1: Load metadata
    print("\n1. Loading iPhone 17 Pro metadata...")
    videos = load_metadata("iPhone 17 Pro")
    print(f"   Loaded {len(videos)} videos")
    
    # Test 2: Search
    print("\n2. Searching for 'camera'...")
    results = search_metadata("camera", "iPhone 17 Pro")
    print(f"   Found {len(results)} results")
    
    # Test 3: Top videos
    print("\n3. Getting top 5 videos by views...")
    top_videos = get_top_videos("iPhone 17 Pro", "viewCount", 5)
    print(f"   Top {len(top_videos)} videos:")
    for i, video in enumerate(top_videos, 1):
        title = video['details']['snippet']['title']
        views = video['details']['statistics']['viewCount']
        print(f"     {i}. {title[:50]}... ({views} views)")
    
    # Test 4: Trends
    print("\n4. Getting temporal trends...")
    trends = get_temporal_trends("iPhone 17 Pro", "viewCount", 7)
    print(f"   Growth rate: {trends['growth_rate']:.2f}%")
    print(f"   Total videos: {trends['total_videos']}")
    
    print("\n✅ All tests completed!")
