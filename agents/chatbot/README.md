# YouTube Analytics Agentic Chatbot System

## Overview

An advanced multi-agent system built with Google Agent Development Kit (ADK) for comprehensive YouTube video analysis. The system leverages collected data on product launches (iPhone 17, iPhone 17 Pro, MacBook Pro 14-inch M5, ChatGPT GPT-5) to provide deep insights into public sentiment, trends, and market positioning.

## System Architecture

### 7 Specialized Agents

#### 1. **YTMetaDataQueryBot**
Handles video metadata queries and engagement metrics.
- **Capabilities:**
  - Search videos by keywords
  - Find top-performing videos by metrics (views, likes, comments)
  - Analyze channel-level performance
  - Calculate engagement rates and ratios
  - Identify top creators and content patterns

#### 2. **RelevancyTranscriptRetriever**
Analyzes video transcripts and spoken content.
- **Capabilities:**
  - Single and multi-term transcript search
  - Topic extraction using frequency analysis
  - Discussion pattern identification
  - Cross-video content comparison
  - Transcript statistics and coverage analysis

#### 3. **RealtimeMetadataAgent**
Fetches live channel information via YouTube API.
- **Capabilities:**
  - Current subscriber counts
  - Real-time channel statistics
  - Batch channel data retrieval
  - Live performance metrics

#### 4. **SentimentAnalysisAgent**
Performs comprehensive sentiment analysis.
- **Capabilities:**
  - Video-specific sentiment analysis
  - Product-level sentiment aggregation
  - Temporal sentiment tracking
  - Extreme opinion identification (most positive/negative)
  - Sentiment distribution analysis
  - Trend detection (improving/declining)

#### 5. **PlottingAgent**
Creates advanced data visualizations.
- **Capabilities:**
  - Time series plots (trends over time)
  - Comparison bar charts (product vs product)
  - Sentiment distribution pie charts
  - Multi-product trend lines
  - Heatmap visualizations
  - High-quality exportable images (300 DPI)

#### 6. **ComparativeAnalysisAgent** *(NEW)*
Performs cross-product comparative analysis.
- **Capabilities:**
  - Multi-product metric comparison
  - Sentiment comparison across products
  - Topic coverage comparison
  - Competitive positioning analysis
  - Market insights and recommendations

#### 7. **TemporalAnalysisAgent** *(NEW)*
Analyzes trends and changes over time.
- **Capabilities:**
  - Temporal trend detection
  - Growth rate calculations
  - Sentiment evolution tracking
  - Pattern identification
  - Inflection point detection

#### **CoordinatorAgent** (Orchestrator)
Intelligent orchestration layer that routes queries and synthesizes multi-agent responses.

## Enhanced Toolset

### Metadata Tools
- `search_metadata()` - Keyword-based video search
- `get_top_videos()` - Top N videos by metric
- `get_temporal_trends()` - Time-series trend analysis *(NEW)*
- `get_channel_insights()` - Channel performance analysis *(NEW)*
- `compare_products()` - Cross-product metric comparison *(NEW)*
- `get_engagement_metrics()` - Comprehensive engagement analysis *(NEW)*

### Transcript Tools
- `search_transcripts()` - Single-term search
- `search_transcripts_multi_term()` - Multi-term AND/OR search *(NEW)*
- `extract_topics()` - Frequency-based topic extraction *(NEW)*
- `compare_transcript_coverage()` - Cross-product topic coverage *(NEW)*
- `get_transcript_statistics()` - Statistical overview *(NEW)*

### Sentiment Tools
- `get_sentiment_for_video()` - Individual video sentiment
- `get_product_sentiment_summary()` - Aggregated product sentiment
- `get_sentiment_over_time()` - Daily sentiment tracking *(NEW)*
- `compare_product_sentiments()` - Cross-product sentiment comparison *(NEW)*
- `get_sentiment_extremes()` - Find most positive/negative videos *(NEW)*
- `analyze_sentiment_distribution()` - Detailed distribution analysis *(NEW)*

### Visualization Tools
- `generate_plot()` - Basic line/bar/scatter plots
- `generate_time_series_plot()` - Temporal trend visualization *(NEW)*
- `generate_comparison_plot()` - Product comparison charts *(NEW)*
- `generate_sentiment_distribution_plot()` - Sentiment pie charts *(NEW)*
- `generate_multi_product_trend_plot()` - Multi-line comparisons *(NEW)*
- `generate_heatmap()` - Matrix visualizations *(NEW)*

### Channel Tools
- `get_channel_info()` - Single channel live data
- `get_channels_info()` - Batch channel data retrieval

## Data Coverage

**Products:**
- iPhone 17 Pro
- MacBook Pro 14-inch M5
- ChatGPT GPT-5

**Time Period:** October 23, 2025 - November 23, 2025 (31 days)

**Data Types:**
- Video metadata (views, likes, comments, titles, descriptions)
- Full video transcripts
- Sentiment analysis (iPhone 17 Pro, ChatGPT GPT-5 only)
- Channel information

## Installation & Setup

### Prerequisites
```bash
# Python 3.10+
python --version

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Environment Configuration
Create a `.env` file in the project root:
```env
# Google AI Studio API Key
GOOGLE_API_KEY=your-google-api-key-here

# YouTube Data API Key
YOUTUBE_API_KEY=your-youtube-api-key-here

# Optional: Vertex AI Configuration
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

## Usage

### Run the Chatbot
```bash
# From the agents/chatbot directory
python main.py
```

### Example Queries

**Basic Queries:**
- "What are the top 5 most viewed iPhone 17 videos?"
- "Show me videos mentioning 'camera quality'"
- "What's the sentiment for iPhone 17 Pro?"

**Comparative Queries:**
- "Compare sentiment between iPhone 17 and iPhone 17 Pro"
- "Which product has better engagement rates?"
- "Compare how battery life is discussed across products"

**Temporal Queries:**
- "How has iPhone 17 sentiment changed over time?"
- "Show me the trend in views for MacBook Pro videos"
- "Is ChatGPT GPT-5 gaining or losing popularity?"

**Analytical Queries:**
- "What topics are most discussed in iPhone 17 reviews?"
- "Find the most positive and most negative reviews for each product"
- "Analyze the sentiment distribution for iPhone 17 Pro"

**Visualization Queries:**
- "Plot sentiment trends over time for all products"
- "Create a comparison chart of average views by product"
- "Show me a heatmap of engagement metrics"

## Key Improvements from Original System

### 1. **Enhanced Data Utilization**
- **Before:** Basic metadata and sentiment queries
- **After:** Temporal analysis, comparative insights, trend detection

### 2. **Advanced Agent Capabilities**
- **Before:** 5 isolated agents with basic functions
- **After:** 7 specialized agents with 24+ advanced tools

### 3. **Cross-Product Intelligence**
- **Before:** Single-product analysis only
- **After:** Comparative analysis, competitive positioning, market insights

### 4. **Temporal Analytics**
- **Before:** Static snapshots
- **After:** Trend tracking, growth rates, sentiment evolution

### 5. **Rich Visualizations**
- **Before:** Basic plots
- **After:** Time series, comparisons, distributions, multi-line trends, heatmaps

### 6. **Intelligent Orchestration**
- **Before:** Simple routing
- **After:** Multi-agent workflows, context synthesis, actionable insights

### 7. **Topic & Content Analysis**
- **Before:** Keyword search only
- **After:** Topic extraction, multi-term search, coverage comparison

### 8. **Sentiment Depth**
- **Before:** Basic sentiment scores
- **After:** Temporal tracking, extremes, distributions, comparative analysis

## Performance Optimizations

- **LRU Caching:** All data loading functions use `@lru_cache` for repeated queries
- **Batch Processing:** Channel info and video details fetched in batches
- **Efficient Data Structures:** Using defaultdict and Counter for aggregations
- **Vectorized Operations:** Pandas for numerical computations

## Architecture Benefits

1. **Modularity:** Each agent is independent and specialized
2. **Scalability:** Easy to add new agents or tools
3. **Maintainability:** Clear separation of concerns
4. **Extensibility:** Tools can be shared across agents
5. **Reliability:** Cached data reduces API calls and improves speed

## Future Enhancements

- Semantic search using embeddings
- Predictive analytics and forecasting
- Real-time data streaming
- Multi-language support
- Export reports (PDF/Excel)
- Interactive dashboards
- A/B testing comparisons
- Influencer impact analysis

## Project Structure

```
agents/chatbot/
├── agents.py              # Agent definitions and orchestration
├── main.py                # CLI entry point
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── tools/
    ├── metadata_search.py    # Metadata analysis tools
    ├── transcript_search.py  # Transcript analysis tools
    ├── sentiment_analysis.py # Sentiment analysis tools
    ├── plotting.py           # Visualization tools
    └── channel_info.py       # Live channel data tools
```

## Contributing

This system is built for the Kaggle Capstone Project. For improvements or bug fixes, please ensure:
- All tools have type hints
- Functions include docstrings
- New agents are properly integrated with the coordinator
- Test queries work as expected

## License

Part of the Kaggle Capstone Project.

---

**Built with Google Agent Development Kit (ADK) and Gemini 2.0 Flash**
