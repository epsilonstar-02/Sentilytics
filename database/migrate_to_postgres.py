"""
Data Migration Script: JSON to PostgreSQL
Migrates YouTube analytics data from JSON files to PostgreSQL database

Usage:
    python migrate_to_postgres.py
"""

import os
import json
import glob
import sys
from datetime import datetime
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_batch
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_config import get_db_connection, DB_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SENTIMENT_DIR = BASE_DIR / "sentiment_data"

# Product mapping
PRODUCT_MAPPING = {
    "iPhone_17_Pro": "iPhone 17 Pro",
    "MacBook_Pro_14-inch_M5": "MacBook Pro 14-inch M5",
    "ChatGPT_GPT-5": "ChatGPT GPT-5"
}


class MigrationStats:
    """Track migration statistics"""
    def __init__(self):
        self.products_inserted = 0
        self.channels_inserted = 0
        self.videos_inserted = 0
        self.transcripts_inserted = 0
        self.sentiment_inserted = 0
        self.errors = []
        self.skipped = {
            'videos': 0,
            'transcripts': 0,
            'sentiment': 0
        }
    
    def print_summary(self):
        """Print migration summary"""
        logger.info("="*70)
        logger.info("MIGRATION SUMMARY")
        logger.info("="*70)
        logger.info(f"✅ Products inserted:     {self.products_inserted}")
        logger.info(f"✅ Channels inserted:     {self.channels_inserted}")
        logger.info(f"✅ Videos inserted:       {self.videos_inserted}")
        logger.info(f"✅ Transcripts inserted:  {self.transcripts_inserted}")
        logger.info(f"✅ Sentiment inserted:    {self.sentiment_inserted}")
        logger.info(f"⚠️  Videos skipped:        {self.skipped['videos']}")
        logger.info(f"⚠️  Transcripts skipped:   {self.skipped['transcripts']}")
        logger.info(f"⚠️  Sentiment skipped:     {self.skipped['sentiment']}")
        if self.errors:
            logger.info(f"❌ Errors encountered:    {len(self.errors)}")
            for error in self.errors[:5]:  # Show first 5 errors
                logger.error(f"   - {error}")
        logger.info("="*70)


def get_product_id(cursor, normalized_name):
    """Get product ID from normalized name"""
    cursor.execute(
        "SELECT id FROM products WHERE normalized_name = %s",
        (normalized_name,)
    )
    result = cursor.fetchone()
    return result[0] if result else None


def insert_or_get_channel(cursor, channel_id, channel_title):
    """Insert channel if not exists, return channel_id"""
    if not channel_id:
        return None
    
    try:
        cursor.execute(
            """
            INSERT INTO channels (channel_id, channel_title)
            VALUES (%s, %s)
            ON CONFLICT (channel_id) DO UPDATE 
            SET channel_title = EXCLUDED.channel_title
            RETURNING channel_id
            """,
            (channel_id, channel_title)
        )
        return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"Error inserting channel {channel_id}: {e}")
        return channel_id


def parse_duration(duration_str):
    """Parse ISO 8601 duration (e.g., PT10M30S) to seconds"""
    if not duration_str or not duration_str.startswith('PT'):
        return None
    return duration_str  # Store as-is for now


def migrate_metadata(conn, cursor, stats):
    """Migrate video metadata from JSON files"""
    logger.info("Migrating video metadata...")
    
    metadata_dir = DATA_DIR / "metadata"
    if not metadata_dir.exists():
        logger.warning(f"Metadata directory not found: {metadata_dir}")
        return
    
    videos_batch = []
    batch_size = 100
    
    for product_dir in metadata_dir.iterdir():
        if not product_dir.is_dir():
            continue
        
        product_normalized = product_dir.name
        product_id = get_product_id(cursor, product_normalized)
        
        if not product_id:
            logger.error(f"Product not found: {product_normalized}")
            continue
        
        logger.info(f"Processing metadata for: {product_normalized}")
        
        for json_file in sorted(product_dir.glob("*.json")):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if not isinstance(data, list):
                    data = [data]
                
                for item in data:
                    try:
                        video_id = item.get('video_id')
                        if not video_id:
                            continue
                        
                        details = item.get('details', {})
                        snippet = details.get('snippet', {})
                        statistics = details.get('statistics', {})
                        content_details = details.get('contentDetails', {})
                        
                        # Extract channel info
                        channel_id = snippet.get('channelId')
                        channel_title = snippet.get('channelTitle')
                        if channel_id:
                            insert_or_get_channel(cursor, channel_id, channel_title)
                            stats.channels_inserted += 1
                        
                        # Prepare video data
                        video_data = {
                            'video_id': video_id,
                            'product_id': product_id,
                            'channel_id': channel_id,
                            'title': snippet.get('title', ''),
                            'description': snippet.get('description', ''),
                            'url': f"https://www.youtube.com/watch?v={video_id}",
                            'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url'),
                            'published_at': snippet.get('publishedAt'),
                            'date': item.get('date'),
                            'category_id': snippet.get('categoryId'),
                            'duration': parse_duration(content_details.get('duration')),
                            'language': snippet.get('defaultAudioLanguage'),
                            'view_count': int(statistics.get('viewCount', 0)),
                            'like_count': int(statistics.get('likeCount', 0)),
                            'comment_count': int(statistics.get('commentCount', 0)),
                            'raw_details': json.dumps(details)
                        }
                        
                        videos_batch.append(video_data)
                        
                        # Insert in batches
                        if len(videos_batch) >= batch_size:
                            insert_videos_batch(cursor, videos_batch, stats)
                            videos_batch = []
                            conn.commit()
                    
                    except Exception as e:
                        stats.errors.append(f"Error processing video {item.get('video_id')}: {e}")
                        stats.skipped['videos'] += 1
            
            except Exception as e:
                logger.error(f"Error reading file {json_file}: {e}")
    
    # Insert remaining videos
    if videos_batch:
        insert_videos_batch(cursor, videos_batch, stats)
        conn.commit()


def insert_videos_batch(cursor, videos_batch, stats):
    """Insert a batch of videos"""
    insert_query = """
        INSERT INTO videos (
            video_id, product_id, channel_id, title, description, url,
            thumbnail_url, published_at, date, category_id, duration,
            language, view_count, like_count, comment_count, raw_details
        ) VALUES (
            %(video_id)s, %(product_id)s, %(channel_id)s, %(title)s, 
            %(description)s, %(url)s, %(thumbnail_url)s, %(published_at)s,
            %(date)s, %(category_id)s, %(duration)s, %(language)s,
            %(view_count)s, %(like_count)s, %(comment_count)s, %(raw_details)s
        )
        ON CONFLICT (video_id) DO UPDATE SET
            view_count = EXCLUDED.view_count,
            like_count = EXCLUDED.like_count,
            comment_count = EXCLUDED.comment_count,
            updated_at = CURRENT_TIMESTAMP
    """
    
    try:
        execute_batch(cursor, insert_query, videos_batch)
        stats.videos_inserted += len(videos_batch)
        logger.info(f"Inserted {len(videos_batch)} videos (Total: {stats.videos_inserted})")
    except Exception as e:
        logger.error(f"Error inserting video batch: {e}")
        stats.errors.append(f"Batch insert error: {e}")


def migrate_transcripts(conn, cursor, stats):
    """Migrate video transcripts from JSON files"""
    logger.info("Migrating video transcripts...")
    
    transcripts_dir = DATA_DIR / "transcripts"
    if not transcripts_dir.exists():
        logger.warning(f"Transcripts directory not found: {transcripts_dir}")
        return
    
    transcripts_batch = []
    batch_size = 100
    
    for product_dir in transcripts_dir.iterdir():
        if not product_dir.is_dir():
            continue
        
        logger.info(f"Processing transcripts for: {product_dir.name}")
        
        for json_file in sorted(product_dir.glob("*.json")):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if not isinstance(data, list):
                    data = [data]
                
                for item in data:
                    try:
                        video_id = item.get('video_id')
                        transcript = item.get('transcript')
                        
                        if not video_id or not transcript:
                            stats.skipped['transcripts'] += 1
                            continue
                        
                        word_count = len(transcript.split())
                        
                        transcripts_batch.append({
                            'video_id': video_id,
                            'transcript': transcript,
                            'word_count': word_count
                        })
                        
                        # Insert in batches
                        if len(transcripts_batch) >= batch_size:
                            insert_transcripts_batch(cursor, transcripts_batch, stats)
                            transcripts_batch = []
                            conn.commit()
                    
                    except Exception as e:
                        stats.errors.append(f"Error processing transcript {item.get('video_id')}: {e}")
                        stats.skipped['transcripts'] += 1
            
            except Exception as e:
                logger.error(f"Error reading file {json_file}: {e}")
    
    # Insert remaining transcripts
    if transcripts_batch:
        insert_transcripts_batch(cursor, transcripts_batch, stats)
        conn.commit()


def insert_transcripts_batch(cursor, transcripts_batch, stats):
    """Insert a batch of transcripts"""
    insert_query = """
        INSERT INTO transcripts (video_id, transcript, word_count)
        VALUES (%(video_id)s, %(transcript)s, %(word_count)s)
        ON CONFLICT (video_id) DO NOTHING
    """
    
    try:
        execute_batch(cursor, insert_query, transcripts_batch)
        stats.transcripts_inserted += len(transcripts_batch)
        logger.info(f"Inserted {len(transcripts_batch)} transcripts (Total: {stats.transcripts_inserted})")
    except Exception as e:
        logger.error(f"Error inserting transcript batch: {e}")
        stats.errors.append(f"Transcript batch insert error: {e}")


def migrate_sentiment(conn, cursor, stats):
    """Migrate sentiment analysis data from JSON files"""
    logger.info("Migrating sentiment analysis...")
    
    if not SENTIMENT_DIR.exists():
        logger.warning(f"Sentiment directory not found: {SENTIMENT_DIR}")
        return
    
    sentiment_batch = []
    batch_size = 100
    
    for product_dir in SENTIMENT_DIR.iterdir():
        if not product_dir.is_dir():
            continue
        
        logger.info(f"Processing sentiment for: {product_dir.name}")
        
        for json_file in sorted(product_dir.glob("*.json")):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if not isinstance(data, list):
                    data = [data]
                
                for item in data:
                    try:
                        video_id = item.get('video_id')
                        sentiment_data = item.get('sentiment_analysis', {})
                        
                        if not video_id or not sentiment_data:
                            stats.skipped['sentiment'] += 1
                            continue
                        
                        # Handle pros/cons - they might be dicts for product comparisons
                        pros = sentiment_data.get('pros', [])
                        cons = sentiment_data.get('cons', [])
                        
                        # Convert dict to array of strings if needed
                        if isinstance(pros, dict):
                            pros_list = []
                            for product, items in pros.items():
                                pros_list.append(f"{product}: {', '.join(items) if isinstance(items, list) else items}")
                            pros = pros_list
                        
                        if isinstance(cons, dict):
                            cons_list = []
                            for product, items in cons.items():
                                cons_list.append(f"{product}: {', '.join(items) if isinstance(items, list) else items}")
                            cons = cons_list
                        
                        # Ensure pros/cons are lists of strings
                        if not isinstance(pros, list):
                            pros = []
                        if not isinstance(cons, list):
                            cons = []
                        
                        sentiment_batch.append({
                            'video_id': video_id,
                            'sentiment': sentiment_data.get('sentiment', 'Neutral'),
                            'score': float(sentiment_data.get('score', 5.0)),
                            'pros': pros,
                            'cons': cons,
                            'summary': sentiment_data.get('summary', '')
                        })
                        
                        # Insert in batches
                        if len(sentiment_batch) >= batch_size:
                            insert_sentiment_batch(cursor, sentiment_batch, stats)
                            sentiment_batch = []
                            conn.commit()
                    
                    except Exception as e:
                        stats.errors.append(f"Error processing sentiment {item.get('video_id')}: {e}")
                        stats.skipped['sentiment'] += 1
            
            except Exception as e:
                logger.error(f"Error reading file {json_file}: {e}")
    
    # Insert remaining sentiment data
    if sentiment_batch:
        insert_sentiment_batch(cursor, sentiment_batch, stats)
        conn.commit()


def insert_sentiment_batch(cursor, sentiment_batch, stats):
    """Insert a batch of sentiment analysis"""
    insert_query = """
        INSERT INTO sentiment_analysis (video_id, sentiment, score, pros, cons, summary)
        VALUES (%(video_id)s, %(sentiment)s, %(score)s, %(pros)s, %(cons)s, %(summary)s)
        ON CONFLICT (video_id) DO UPDATE SET
            sentiment = EXCLUDED.sentiment,
            score = EXCLUDED.score,
            pros = EXCLUDED.pros,
            cons = EXCLUDED.cons,
            summary = EXCLUDED.summary,
            analyzed_at = CURRENT_TIMESTAMP
    """
    
    try:
        execute_batch(cursor, insert_query, sentiment_batch)
        stats.sentiment_inserted += len(sentiment_batch)
        logger.info(f"Inserted {len(sentiment_batch)} sentiment records (Total: {stats.sentiment_inserted})")
    except Exception as e:
        logger.error(f"Error inserting sentiment batch: {e}")
        stats.errors.append(f"Sentiment batch insert error: {e}")


def verify_migration(cursor):
    """Verify the migration by checking record counts"""
    logger.info("\nVerifying migration...")
    
    queries = {
        'Products': "SELECT COUNT(*) FROM products",
        'Channels': "SELECT COUNT(*) FROM channels",
        'Videos': "SELECT COUNT(*) FROM videos",
        'Transcripts': "SELECT COUNT(*) FROM transcripts",
        'Sentiment': "SELECT COUNT(*) FROM sentiment_analysis"
    }
    
    logger.info("="*70)
    logger.info("DATABASE RECORD COUNTS")
    logger.info("="*70)
    
    for name, query in queries.items():
        cursor.execute(query)
        count = cursor.fetchone()[0]
        logger.info(f"{name:20s}: {count:,}")
    
    # Check product stats
    cursor.execute("SELECT * FROM product_stats")
    products = cursor.fetchall()
    
    logger.info("="*70)
    logger.info("PRODUCT STATISTICS")
    logger.info("="*70)
    
    for product in products:
        logger.info(f"\n{product[1]}:")  # product name
        logger.info(f"  Total Videos:      {product[3]:,}")
        logger.info(f"  Total Views:       {product[4]:,}")
        logger.info(f"  Avg Sentiment:     {product[8]:.2f}" if product[8] else "  Avg Sentiment:     N/A")
        logger.info(f"  Channels:          {product[9]:,}")
    
    logger.info("="*70)


def main():
    """Main migration function"""
    logger.info("="*70)
    logger.info("YouTube Analytics: JSON to PostgreSQL Migration")
    logger.info("="*70)
    
    # Check database connection
    logger.info(f"\nConnecting to database: {DB_CONFIG['database']}")
    logger.info(f"Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        logger.info("✅ Connected successfully!\n")
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        logger.error("\nPlease ensure:")
        logger.error("  1. PostgreSQL is running")
        logger.error("  2. Database 'youtube_analytics' exists")
        logger.error("  3. Schema has been created (run schema.sql)")
        logger.error("  4. Database credentials in .env are correct")
        return
    
    stats = MigrationStats()
    
    try:
        # Verify products exist
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        if product_count == 0:
            logger.error("❌ No products found in database!")
            logger.error("Please run schema.sql first to create tables and insert products.")
            return
        
        logger.info(f"Found {product_count} products in database\n")
        stats.products_inserted = product_count
        
        # Start migration
        start_time = datetime.now()
        
        # 1. Migrate metadata (videos and channels)
        migrate_metadata(conn, cursor, stats)
        
        # 2. Migrate transcripts
        migrate_transcripts(conn, cursor, stats)
        
        # 3. Migrate sentiment analysis
        migrate_sentiment(conn, cursor, stats)
        
        # Commit final changes
        conn.commit()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Print summary
        stats.print_summary()
        logger.info(f"⏱️  Migration completed in {duration:.2f} seconds\n")
        
        # Verify migration
        verify_migration(cursor)
        
        logger.info("\n✅ Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    
    finally:
        cursor.close()
        conn.close()
        logger.info("\nDatabase connection closed.")


if __name__ == "__main__":
    main()
