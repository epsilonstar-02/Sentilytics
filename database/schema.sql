-- PostgreSQL Database Schema for YouTube Analytics
-- Author: Database Migration Script
-- Date: November 26, 2025

-- Drop existing tables if they exist (for clean migration)
DROP TABLE IF EXISTS sentiment_analysis CASCADE;
DROP TABLE IF EXISTS transcripts CASCADE;
DROP TABLE IF EXISTS videos CASCADE;
DROP TABLE IF EXISTS channels CASCADE;
DROP TABLE IF EXISTS products CASCADE;

-- ============================================================================
-- Table 1: Products
-- ============================================================================
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    normalized_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    icon VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert the three products
INSERT INTO products (name, normalized_name, description, icon) VALUES
('iPhone 17 Pro', 'iPhone_17_Pro', 'Apple iPhone 17 Pro smartphone', '📱'),
('MacBook Pro 14-inch M5', 'MacBook_Pro_14-inch_M5', 'Apple MacBook Pro with M5 chip', '💻'),
('ChatGPT GPT-5', 'ChatGPT_GPT-5', 'OpenAI ChatGPT GPT-5 AI assistant', '🤖');

-- ============================================================================
-- Table 2: Channels
-- ============================================================================
CREATE TABLE channels (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(50) UNIQUE NOT NULL,
    channel_title VARCHAR(200),
    total_videos INTEGER DEFAULT 0,
    total_views BIGINT DEFAULT 0,
    total_likes BIGINT DEFAULT 0,
    avg_sentiment_score DECIMAL(4,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_channels_channel_id ON channels(channel_id);
CREATE INDEX idx_channels_total_videos ON channels(total_videos);

-- ============================================================================
-- Table 3: Videos (Main table)
-- ============================================================================
CREATE TABLE videos (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(50) UNIQUE NOT NULL,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    channel_id VARCHAR(50) REFERENCES channels(channel_id) ON DELETE SET NULL,
    
    -- Basic Info
    title TEXT NOT NULL,
    description TEXT,
    url TEXT,
    thumbnail_url TEXT,
    
    -- Dates
    published_at TIMESTAMP,
    date DATE,
    
    -- Classification
    category_id VARCHAR(10),
    duration VARCHAR(20),
    language VARCHAR(10),
    
    -- Statistics
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    
    -- Raw Data (for flexibility)
    raw_details JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_view_count CHECK (view_count >= 0),
    CONSTRAINT chk_like_count CHECK (like_count >= 0),
    CONSTRAINT chk_comment_count CHECK (comment_count >= 0)
);

-- Indexes for videos table
CREATE INDEX idx_videos_video_id ON videos(video_id);
CREATE INDEX idx_videos_product_id ON videos(product_id);
CREATE INDEX idx_videos_channel_id ON videos(channel_id);
CREATE INDEX idx_videos_date ON videos(date);
CREATE INDEX idx_videos_published_at ON videos(published_at);
CREATE INDEX idx_videos_view_count ON videos(view_count DESC);
CREATE INDEX idx_videos_like_count ON videos(like_count DESC);
CREATE INDEX idx_videos_product_date ON videos(product_id, date);
CREATE INDEX idx_videos_title ON videos USING gin(to_tsvector('english', title));

-- JSONB index for raw_details
CREATE INDEX idx_videos_raw_details ON videos USING gin(raw_details);

-- ============================================================================
-- Table 4: Transcripts
-- ============================================================================
CREATE TABLE transcripts (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(50) UNIQUE NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,
    transcript TEXT NOT NULL,
    word_count INTEGER,
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_transcript_length CHECK (char_length(transcript) > 0)
);

-- Indexes for transcripts
CREATE INDEX idx_transcripts_video_id ON transcripts(video_id);
-- Full-text search index (most important for transcript searches)
CREATE INDEX idx_transcripts_fulltext ON transcripts 
    USING gin(to_tsvector('english', transcript));

-- ============================================================================
-- Table 5: Sentiment Analysis
-- ============================================================================
CREATE TABLE sentiment_analysis (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(50) UNIQUE NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,
    
    -- Sentiment
    sentiment VARCHAR(20) NOT NULL,  -- Positive, Negative, Neutral
    score DECIMAL(4,2) CHECK (score >= 0 AND score <= 10),
    
    -- Details
    pros TEXT[],  -- Array of positive points
    cons TEXT[],  -- Array of negative points
    summary TEXT,
    
    -- Metadata
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(50),
    
    CONSTRAINT chk_sentiment_value CHECK (sentiment IN ('Positive', 'Negative', 'Neutral'))
);

-- Indexes for sentiment_analysis
CREATE INDEX idx_sentiment_video_id ON sentiment_analysis(video_id);
CREATE INDEX idx_sentiment_sentiment ON sentiment_analysis(sentiment);
CREATE INDEX idx_sentiment_score ON sentiment_analysis(score DESC);

-- ============================================================================
-- Views for Common Queries
-- ============================================================================

-- View: Video Details with Product and Sentiment
CREATE VIEW video_details AS
SELECT 
    v.id,
    v.video_id,
    v.title,
    v.description,
    v.url,
    v.date,
    v.published_at,
    v.view_count,
    v.like_count,
    v.comment_count,
    v.duration,
    p.name AS product_name,
    p.normalized_name AS product_normalized_name,
    c.channel_title,
    c.channel_id,
    s.sentiment,
    s.score AS sentiment_score,
    s.pros,
    s.cons,
    s.summary AS sentiment_summary,
    CASE 
        WHEN v.like_count > 0 AND v.view_count > 0 
        THEN ROUND((v.like_count::DECIMAL / v.view_count) * 100, 2)
        ELSE 0
    END AS engagement_rate
FROM videos v
JOIN products p ON v.product_id = p.id
LEFT JOIN channels c ON v.channel_id = c.channel_id
LEFT JOIN sentiment_analysis s ON v.video_id = s.video_id;

-- View: Product Statistics
CREATE VIEW product_stats AS
SELECT 
    p.id,
    p.name,
    p.normalized_name,
    COUNT(DISTINCT v.video_id) AS total_videos,
    SUM(v.view_count) AS total_views,
    SUM(v.like_count) AS total_likes,
    AVG(v.view_count)::INTEGER AS avg_views,
    AVG(v.like_count)::INTEGER AS avg_likes,
    AVG(s.score) AS avg_sentiment_score,
    COUNT(DISTINCT v.channel_id) AS total_channels,
    MIN(v.date) AS first_video_date,
    MAX(v.date) AS last_video_date
FROM products p
LEFT JOIN videos v ON p.id = v.product_id
LEFT JOIN sentiment_analysis s ON v.video_id = s.video_id
GROUP BY p.id, p.name, p.normalized_name;

-- View: Daily Product Metrics
CREATE VIEW daily_product_metrics AS
SELECT 
    p.name AS product_name,
    v.date,
    COUNT(v.video_id) AS video_count,
    SUM(v.view_count) AS total_views,
    AVG(v.view_count)::INTEGER AS avg_views,
    SUM(v.like_count) AS total_likes,
    AVG(s.score) AS avg_sentiment_score,
    COUNT(CASE WHEN s.sentiment = 'Positive' THEN 1 END) AS positive_count,
    COUNT(CASE WHEN s.sentiment = 'Negative' THEN 1 END) AS negative_count,
    COUNT(CASE WHEN s.sentiment = 'Neutral' THEN 1 END) AS neutral_count
FROM products p
JOIN videos v ON p.id = v.product_id
LEFT JOIN sentiment_analysis s ON v.video_id = s.video_id
GROUP BY p.name, v.date
ORDER BY p.name, v.date;

-- View: Channel Rankings
CREATE VIEW channel_rankings AS
SELECT 
    c.channel_id,
    c.channel_title,
    COUNT(DISTINCT v.video_id) AS video_count,
    SUM(v.view_count) AS total_views,
    AVG(v.view_count)::INTEGER AS avg_views_per_video,
    AVG(s.score) AS avg_sentiment_score,
    STRING_AGG(DISTINCT p.name, ', ') AS products_covered
FROM channels c
JOIN videos v ON c.channel_id = v.channel_id
LEFT JOIN products p ON v.product_id = p.id
LEFT JOIN sentiment_analysis s ON v.video_id = s.video_id
GROUP BY c.channel_id, c.channel_title
ORDER BY video_count DESC;

-- ============================================================================
-- Functions
-- ============================================================================

-- Function: Update channel statistics
CREATE OR REPLACE FUNCTION update_channel_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE channels c
    SET 
        total_videos = (
            SELECT COUNT(*) FROM videos WHERE channel_id = NEW.channel_id
        ),
        total_views = (
            SELECT COALESCE(SUM(view_count), 0) FROM videos WHERE channel_id = NEW.channel_id
        ),
        total_likes = (
            SELECT COALESCE(SUM(like_count), 0) FROM videos WHERE channel_id = NEW.channel_id
        ),
        avg_sentiment_score = (
            SELECT AVG(s.score)
            FROM videos v
            JOIN sentiment_analysis s ON v.video_id = s.video_id
            WHERE v.channel_id = NEW.channel_id
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE channel_id = NEW.channel_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Update channel stats when video is inserted/updated
CREATE TRIGGER trg_update_channel_stats
AFTER INSERT OR UPDATE ON videos
FOR EACH ROW
EXECUTE FUNCTION update_channel_stats();

-- Function: Update video updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update updated_at for videos
CREATE TRIGGER trg_videos_updated_at
BEFORE UPDATE ON videos
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Trigger: Auto-update updated_at for channels
CREATE TRIGGER trg_channels_updated_at
BEFORE UPDATE ON channels
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Sample Queries (for testing)
-- ============================================================================

-- Get top 10 videos by views for a product
-- SELECT * FROM video_details WHERE product_name = 'iPhone 17 Pro' ORDER BY view_count DESC LIMIT 10;

-- Get sentiment distribution for a product
-- SELECT sentiment, COUNT(*) FROM video_details WHERE product_name = 'iPhone 17 Pro' GROUP BY sentiment;

-- Get daily sentiment trends
-- SELECT date, AVG(sentiment_score) as avg_score FROM video_details WHERE product_name = 'iPhone 17 Pro' GROUP BY date ORDER BY date;

-- Full-text search in transcripts
-- SELECT v.*, t.transcript FROM videos v JOIN transcripts t ON v.video_id = t.video_id WHERE to_tsvector('english', t.transcript) @@ to_tsquery('english', 'battery & life');

-- Get product comparison
-- SELECT * FROM product_stats ORDER BY total_views DESC;

-- ============================================================================
-- Grants (adjust based on your user setup)
-- ============================================================================

-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO youtube_analytics_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO youtube_analytics_user;

-- ============================================================================
-- End of Schema
-- ============================================================================

-- Display confirmation
SELECT 'YouTube Analytics Database Schema Created Successfully!' AS status;
SELECT 'Products:', COUNT(*) FROM products;
SELECT 'Ready for data migration!' AS next_step;
