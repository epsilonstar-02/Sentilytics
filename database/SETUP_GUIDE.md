# PostgreSQL Setup and Migration Guide

## 📋 Prerequisites

- PostgreSQL 12+ installed
- Python 3.8+
- All project dependencies installed

---

## 🚀 Step-by-Step Setup

### Step 1: Install PostgreSQL

#### macOS (Using Homebrew):
```bash
brew install postgresql@15
brew services start postgresql@15
```

> [!NOTE]
> **PostgreSQL 15 PATH Configuration (macOS)**
> 
> PostgreSQL 15 is installed as "keg-only" by Homebrew, which means the `psql` command won't be in your PATH by default. You need to add it manually:
> 
> ```bash
> # Add PostgreSQL 15 to your PATH (add this to ~/.zshrc or ~/.bash_profile)
> echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
> 
> # Reload your shell configuration
> source ~/.zshrc
> ```
> 
> **Verify Installation:**
> ```bash
> psql --version
> # Expected output: psql (PostgreSQL) 15.15 (Homebrew)
> ```
> 
> **Start PostgreSQL Service:**
> ```bash
> brew services start postgresql@15
> ```

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

#### Windows:
Download and install from: https://www.postgresql.org/download/windows/

---

### Step 2: Create Database

```bash
# Login to PostgreSQL (default user is 'postgres')
psql -U postgres

# Or on macOS with Homebrew:
psql postgres
```

Inside PostgreSQL shell:
```sql
-- Create database
CREATE DATABASE youtube_analytics;

-- Create user (optional, for better security)
CREATE USER youtube_user WITH PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE youtube_analytics TO youtube_user;

-- Grant superuser privileges (if needed for full access)
ALTER ROLE youtube_user 
  WITH SUPERUSER CREATEDB CREATEROLE REPLICATION BYPASSRLS LOGIN;

-- Exit
\q
```

---

### Step 3: Configure Environment Variables

Create or update `.env` file in project root:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=youtube_analytics
DB_USER=postgres
DB_PASSWORD=your_password_here

# Existing API keys (don't remove these)
GOOGLE_API_KEY=your_google_api_key
YOUTUBE_API_KEY=your_youtube_api_key
```

---

### Step 4: Install Python Dependencies

```bash
# Navigate to database directory
cd database

# Install database-specific requirements
pip install -r requirements.txt

# Or install them individually:
pip install psycopg2-binary sqlalchemy
```

---

### Step 5: Create Database Schema

```bash
# Connect to PostgreSQL and run schema
psql -U postgres -d youtube_analytics -f schema.sql

# Or using the command line directly:
psql -U postgres -d youtube_analytics < schema.sql
```

Expected output:
```
CREATE TABLE
CREATE TABLE
...
INSERT 0 3
CREATE INDEX
...
       status        
----------------------
 Database Created!
```

---

### Step 6: Test Database Connection

```bash
# Run the configuration test
python db_config.py
```

Expected output:
```
============================================================
YouTube Analytics - Database Configuration Test
============================================================

Connection String: postgresql://postgres:****@localhost:5432/youtube_analytics

Testing connection...
✅ Database connection successful!

Products in database: 3
  - iPhone 17 Pro
  - MacBook Pro 14-inch M5
  - ChatGPT GPT-5

============================================================
```

---

### Step 7: Run Data Migration

```bash
# Run the migration script
python migrate_to_postgres.py
```

This will:
1. ✅ Load all JSON files
2. ✅ Parse video metadata
3. ✅ Extract transcripts
4. ✅ Import sentiment analysis
5. ✅ Create relationships
6. ✅ Verify data integrity

Expected output:
```
======================================================================
YouTube Analytics: JSON to PostgreSQL Migration
======================================================================

Connecting to database: youtube_analytics
Host: localhost:5432
✅ Connected successfully!

Found 3 products in database

Migrating video metadata...
Processing metadata for: iPhone_17_Pro
Inserted 100 videos (Total: 100)
Inserted 100 videos (Total: 200)
...

Migrating video transcripts...
Processing transcripts for: iPhone_17_Pro
Inserted 100 transcripts (Total: 100)
...

Migrating sentiment analysis...
Processing sentiment for: iPhone_17_Pro
Inserted 100 sentiment records (Total: 100)
...

======================================================================
MIGRATION SUMMARY
======================================================================
✅ Products inserted:     3
✅ Channels inserted:     1247
✅ Videos inserted:       6000
✅ Transcripts inserted:  5800
✅ Sentiment inserted:    5800
⚠️  Videos skipped:        0
⚠️  Transcripts skipped:   200
⚠️  Sentiment skipped:     200
======================================================================
⏱️  Migration completed in 45.67 seconds

Verifying migration...
======================================================================
DATABASE RECORD COUNTS
======================================================================
Products            : 3
Channels            : 1,247
Videos              : 6,000
Transcripts         : 5,800
Sentiment           : 5,800
======================================================================

✅ Migration completed successfully!
```

---

## 🔍 Verify Migration

### Check Tables:
```bash
psql -U postgres -d youtube_analytics
```

```sql
-- Check products
SELECT * FROM products;

-- Check video count by product
SELECT 
    p.name, 
    COUNT(v.id) as video_count,
    SUM(v.view_count) as total_views
FROM products p
LEFT JOIN videos v ON p.id = v.product_id
GROUP BY p.name;

-- Check sentiment distribution
SELECT 
    sentiment, 
    COUNT(*) as count,
    AVG(score) as avg_score
FROM sentiment_analysis
GROUP BY sentiment;

-- Check full-text search on transcripts
SELECT v.title, t.transcript
FROM videos v
JOIN transcripts t ON v.video_id = t.video_id
WHERE to_tsvector('english', t.transcript) @@ to_tsquery('english', 'battery & life')
LIMIT 5;
```

---

## 📊 Useful Queries

### Get top 10 videos by views:
```sql
SELECT 
    title,
    view_count,
    like_count,
    published_at
FROM videos
ORDER BY view_count DESC
LIMIT 10;
```

### Get sentiment trends over time:
```sql
SELECT 
    date,
    AVG(score) as avg_sentiment,
    COUNT(*) as video_count
FROM videos v
JOIN sentiment_analysis s ON v.video_id = s.video_id
WHERE v.product_id = (SELECT id FROM products WHERE name = 'iPhone 17 Pro')
GROUP BY date
ORDER BY date;
```

### Get channel rankings:
```sql
SELECT * FROM channel_rankings ORDER BY video_count DESC LIMIT 10;
```

### Search transcripts:
```sql
SELECT 
    v.title,
    v.url,
    ts_headline('english', t.transcript, to_tsquery('english', 'battery')) as snippet
FROM videos v
JOIN transcripts t ON v.video_id = t.video_id
WHERE to_tsvector('english', t.transcript) @@ to_tsquery('english', 'battery')
LIMIT 5;
```

---

## 🔧 Troubleshooting

### Connection Refused
```bash
# Check if PostgreSQL is running
pg_isready

# On macOS:
brew services list

# On Ubuntu:
sudo systemctl status postgresql
```

### Authentication Failed
```bash
# Reset PostgreSQL password (macOS/Linux):
psql postgres -c "ALTER USER postgres PASSWORD 'new_password';"
```

### Database Not Found
```sql
-- List all databases
\l

-- Create database if missing
CREATE DATABASE youtube_analytics;
```

### Permission Denied
```sql
-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE youtube_analytics TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
```

### Migration Errors

#### "Products not found":
```bash
# Re-run schema.sql
psql -U postgres -d youtube_analytics -f schema.sql
```

#### "Foreign key violation":
- Check that schema was created completely
- Verify products exist in database

#### "Out of memory":
- Reduce batch_size in migrate_to_postgres.py
- Process one product at a time

---

## 🎯 Next Steps

After successful migration:

1. ✅ **Update Application Code**
   - Modify `agents/chatbot/tools/*.py` to use PostgreSQL
   - Update caching strategy
   - Test all features

2. ✅ **Performance Optimization**
   - Add more indexes if needed
   - Tune PostgreSQL settings
   - Monitor query performance

3. ✅ **Backup Strategy**
   ```bash
   # Backup database
   pg_dump -U postgres youtube_analytics > backup.sql
   
   # Restore database
   psql -U postgres youtube_analytics < backup.sql
   ```

4. ✅ **Monitoring**
   - Set up query logging
   - Monitor connection pool
   - Track slow queries

---

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)

---

## 🆘 Getting Help

If you encounter issues:

1. Check logs in terminal output
2. Verify `.env` configuration
3. Check PostgreSQL logs: `/usr/local/var/log/postgresql@15/` (macOS)
4. Test connection with `python db_config.py`

---

**Ready to start? Follow the steps above in order!** 🚀
