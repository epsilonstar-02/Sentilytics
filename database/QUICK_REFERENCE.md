# PostgreSQL Quick Reference

## 🚀 Quick Start Commands

### Check Database Status
```bash
# Is PostgreSQL running?
pg_isready

# Connect to database
psql -d youtube_analytics

# List all tables
psql -d youtube_analytics -c "\dt"

# Check record counts
psql -d youtube_analytics -c "
SELECT 
    'products' as table, COUNT(*) FROM products
UNION ALL SELECT 'channels', COUNT(*) FROM channels
UNION ALL SELECT 'videos', COUNT(*) FROM videos
UNION ALL SELECT 'transcripts', COUNT(*) FROM transcripts
UNION ALL SELECT 'sentiment_analysis', COUNT(*) FROM sentiment_analysis;
"
```

### Python Database Access
```python
# Import and use
from database.db_config import get_db_session
from sqlalchemy import text

# Query example
with get_db_session() as session:
    result = session.execute(text("""
        SELECT p.name, COUNT(v.id) as video_count
        FROM products p
        JOIN videos v ON p.id = v.product_id
        GROUP BY p.name
    """))
    for row in result:
        print(f"{row[0]}: {row[1]} videos")
```

## 📊 Useful Queries

### Product Statistics
```sql
SELECT * FROM product_stats;
```

### Recent Videos
```sql
SELECT 
    p.name as product,
    v.title,
    v.view_count,
    s.sentiment,
    s.score
FROM videos v
JOIN products p ON v.product_id = p.id
LEFT JOIN sentiment_analysis s ON v.video_id = s.video_id
ORDER BY v.published_at DESC
LIMIT 10;
```

### Search Transcripts (Full-Text)
```sql
SELECT 
    v.title,
    ts_headline('english', t.transcript, 
                to_tsquery('english', 'battery & life'),
                'MaxWords=30, MinWords=10') as snippet
FROM transcripts t
JOIN videos v ON t.video_id = v.video_id
WHERE t.transcript_search @@ to_tsquery('english', 'battery & life')
LIMIT 5;
```

### Top Positive Videos
```sql
SELECT 
    v.title,
    v.view_count,
    s.score,
    s.pros
FROM videos v
JOIN sentiment_analysis s ON v.video_id = s.video_id
WHERE s.sentiment = 'Positive' AND s.score >= 8.0
ORDER BY v.view_count DESC
LIMIT 10;
```

### Daily Metrics
```sql
SELECT * FROM daily_product_metrics
ORDER BY date DESC, product_name;
```

## 🔧 Maintenance Commands

### Backup Database
```bash
# Full backup
pg_dump youtube_analytics > backup.sql

# Compressed backup
pg_dump youtube_analytics | gzip > backup_$(date +%Y%m%d).sql.gz

# Backup specific table
pg_dump -t videos youtube_analytics > videos_backup.sql
```

### Restore Database
```bash
# Drop and recreate
dropdb youtube_analytics
createdb youtube_analytics

# Restore from backup
psql youtube_analytics < backup.sql
```

### View Database Size
```sql
SELECT 
    pg_size_pretty(pg_database_size('youtube_analytics')) as total_size,
    pg_size_pretty(pg_total_relation_size('videos')) as videos_size,
    pg_size_pretty(pg_total_relation_size('transcripts')) as transcripts_size;
```

### Analyze Query Performance
```sql
EXPLAIN ANALYZE
SELECT * FROM videos WHERE product_id = 1 ORDER BY view_count DESC LIMIT 10;
```

## 🛠️ Migration & Updates

### Re-run Migration
```bash
cd /Users/avinash/Downloads/Capstone_Project-main/database
/Users/avinash/Downloads/Capstone_Project-main/.venv/bin/python migrate_to_postgres.py
```

### Clear Specific Table
```sql
-- Be careful! This deletes data
DELETE FROM sentiment_analysis;
DELETE FROM transcripts;
DELETE FROM videos;
-- Note: Products and channels are referenced by foreign keys
```

### Add New Product
```sql
INSERT INTO products (name, description)
VALUES ('iPad Pro 13', 'Latest iPad Pro with M5 chip');
```

## 📈 Analytics Queries

### Sentiment Trend Over Time
```sql
SELECT 
    date_trunc('day', v.published_at) as day,
    AVG(s.score) as avg_sentiment,
    COUNT(*) as video_count
FROM videos v
JOIN sentiment_analysis s ON v.video_id = s.video_id
GROUP BY day
ORDER BY day;
```

### Compare Products
```sql
SELECT 
    p.name,
    COUNT(v.id) as total_videos,
    AVG(v.view_count) as avg_views,
    AVG(s.score) as avg_sentiment,
    COUNT(CASE WHEN s.sentiment = 'Positive' THEN 1 END) as positive_count,
    COUNT(CASE WHEN s.sentiment = 'Negative' THEN 1 END) as negative_count
FROM products p
LEFT JOIN videos v ON p.id = v.product_id
LEFT JOIN sentiment_analysis s ON v.video_id = s.video_id
GROUP BY p.name;
```

### Top Keywords in Positive Reviews
```sql
SELECT 
    word,
    COUNT(*) as frequency
FROM (
    SELECT unnest(string_to_array(lower(array_to_string(pros, ' ')), ' ')) as word
    FROM sentiment_analysis
    WHERE sentiment = 'Positive'
) words
WHERE length(word) > 4  -- Ignore short words
GROUP BY word
ORDER BY frequency DESC
LIMIT 20;
```

## 🔍 Troubleshooting

### Connection Issues
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Start PostgreSQL
brew services start postgresql@15

# Check connection
psql -l
```

### Permission Issues
```sql
-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE youtube_analytics TO avinash;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO avinash;
```

### Index Rebuild
```sql
-- If queries are slow, rebuild indexes
REINDEX DATABASE youtube_analytics;

-- Or specific table
REINDEX TABLE videos;
```

### Update Statistics
```sql
-- Help query planner optimize
ANALYZE;

-- Or specific table
ANALYZE videos;
```

## 📝 Schema Information

### View Table Structure
```sql
\d+ videos              -- Detailed table info
\d+ sentiment_analysis  -- With constraints and indexes
```

### View All Indexes
```sql
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

### View Foreign Keys
```sql
SELECT
    tc.constraint_name, 
    tc.table_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

## 🎯 Common Use Cases

### Find Videos Missing Transcripts
```sql
SELECT v.video_id, v.title
FROM videos v
LEFT JOIN transcripts t ON v.video_id = t.video_id
WHERE t.id IS NULL;
```

### Find Videos Missing Sentiment
```sql
SELECT v.video_id, v.title, v.published_at
FROM videos v
LEFT JOIN sentiment_analysis s ON v.video_id = s.video_id
WHERE s.id IS NULL
ORDER BY v.published_at DESC;
```

### Top Channels by Average Sentiment
```sql
SELECT 
    c.channel_title,
    COUNT(v.id) as video_count,
    AVG(s.score) as avg_sentiment
FROM channels c
JOIN videos v ON c.channel_id = v.channel_id
JOIN sentiment_analysis s ON v.video_id = s.video_id
GROUP BY c.channel_title
HAVING COUNT(v.id) >= 5  -- At least 5 videos
ORDER BY avg_sentiment DESC
LIMIT 20;
```

---

**For full documentation, see:**
- `database/README.md` - Overview
- `database/SETUP_GUIDE.md` - Setup instructions
- `MIGRATION_COMPLETE.md` - Migration results
