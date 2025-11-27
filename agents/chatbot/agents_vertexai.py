"""
Chatbot agents configured for Vertex AI with PostgreSQL backend.
This file creates agents that use Vertex AI via environment variables.
"""

import os
from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool

# Import our tools
from agents.chatbot.tools.metadata_search import (
    search_metadata, get_top_videos, get_temporal_trends, 
    get_channel_insights, compare_products, get_engagement_metrics
)
from agents.chatbot.tools.transcript_search import (
    search_transcripts, search_transcripts_multi_term, 
    extract_topics, compare_transcript_coverage, get_transcript_statistics
)
from agents.chatbot.tools.channel_info import get_channel_info, get_channels_info
from agents.chatbot.tools.plotting import (
    generate_plot, generate_time_series_plot, generate_comparison_plot,
    generate_sentiment_distribution_plot, generate_multi_product_trend_plot, generate_heatmap
)
from agents.chatbot.tools.sentiment_analysis import (
    get_sentiment_for_video, get_product_sentiment_summary,
    get_sentiment_over_time, compare_product_sentiments,
    get_sentiment_extremes, analyze_sentiment_distribution
)

# Configure Vertex AI via environment variables
# The Google ADK will automatically use Vertex AI when these are set:
# - GOOGLE_APPLICATION_CREDENTIALS
# - GOOGLE_CLOUD_PROJECT  
# - GOOGLE_CLOUD_LOCATION

# Model configuration - use Vertex AI models
MODEL_NAME = "gemini-2.0-flash-exp"  # or "gemini-1.5-flash" or "gemini-1.5-pro"

# 1. YTMetaDataQueryBot
yt_metadata_agent = LlmAgent(
    name="YTMetaDataQueryBot",
    model=MODEL_NAME,
    description="Answers questions about YouTube video metadata, stats, and engagement metrics.",
    instruction="""
    You are the YTMetaDataQueryBot.
    
    Your responsibilities:
    1. Answer questions about YouTube video metadata (views, likes, comments, titles, publish dates).
    2. Search for videos using keywords.
    3. Identify top-performing videos based on metrics like views or likes.
    4. Analyze channel-level performance and identify top creators.
    5. Calculate engagement metrics and channel insights.
    
    IMPORTANT - Use these EXACT product names when calling tools:
    - "iPhone_17_Pro" (for iPhone 17 Pro)
    - "MacBook_Pro_14-inch_M5" (for MacBook Pro M5)
    - "ChatGPT_GPT-5" (for ChatGPT/GPT-5)
    
    Tools:
    - `search_metadata`: Find videos by keyword in title or description.
    - `get_top_videos`: Find top N videos by metric (viewCount, likeCount, commentCount).
    - `get_channel_insights`: Analyze channel-level performance for a product.
    - `get_engagement_metrics`: Calculate comprehensive engagement metrics.
    
    Always provide context and explanations with your data.
    """,
    output_key="metadata_results",
    tools=[search_metadata, get_top_videos, get_channel_insights, get_engagement_metrics]
)

# 2. RelevancyTranscriptRetriever
transcript_agent = LlmAgent(
    name="RelevancyTranscriptRetriever",
    model=MODEL_NAME,
    description="Searches video transcripts for content, extracts topics, and analyzes discussion patterns.",
    instruction="""
    You are the RelevancyTranscriptRetriever.
    
    Your responsibilities:
    1. Search through video transcripts for specific keywords, phrases, or topics.
    2. Provide the context (snippet) of where terms were spoken.
    3. Identify which videos contain specific content.
    4. Extract common topics discussed across videos.
    5. Analyze multi-term searches and topic coverage.
    
    IMPORTANT - Use these EXACT product names when calling tools:
    - "iPhone_17_Pro" (for iPhone 17 Pro)
    - "MacBook_Pro_14-inch_M5" (for MacBook Pro M5)
    - "ChatGPT_GPT-5" (for ChatGPT/GPT-5)
    
    Tools:
    - `search_transcripts`: Search for a single term within transcripts.
    - `search_transcripts_multi_term`: Search for multiple terms (AND/OR logic).
    - `extract_topics`: Find most frequently discussed topics.
    - `get_transcript_statistics`: Get overview statistics about transcripts.
    
    Always provide the video title and relevant transcript snippets.
    """,
    output_key="transcript_results",
    tools=[search_transcripts, search_transcripts_multi_term, extract_topics, get_transcript_statistics]
)

# 3. RealtimeMetadataAgent
realtime_metadata_agent = LlmAgent(
    name="RealtimeMetadataAgent",
    model=MODEL_NAME,
    description="Retrieves real-time information about YouTube channels, such as subscriber counts.",
    instruction="""
    You are the RealtimeMetadataAgent.
    
    Your responsibilities:
    1. Fetch up-to-date channel statistics (subscribers, total views, video count).
    2. Handle requests for single or multiple channels.
    
    Tools:
    - `get_channel_info`: Get info for one channel ID.
    - `get_channels_info`: Get info for a list of channel IDs.
    
    Note: You need Channel IDs to work. If the user provides a channel name, explain that you need the channel ID.
    """,
    output_key="channel_results",
    tools=[get_channel_info, get_channels_info]
)

# 4. SentimentAnalysisAgent
sentiment_agent = LlmAgent(
    name="SentimentAnalysisAgent",
    model=MODEL_NAME,
    description="Analyzes sentiment, tracks opinion changes, and identifies extreme reviews.",
    instruction="""
    You are the SentimentAnalysisAgent.
    
    Your responsibilities:
    1. Provide sentiment analysis for specific videos (score, pros, cons).
    2. Provide aggregated sentiment summaries for products.
    3. Track sentiment changes over time and identify trends.
    4. Find videos with extreme sentiments (most positive/negative).
    5. Analyze sentiment distribution patterns.
    
    IMPORTANT - Use these EXACT product names when calling tools:
    - "iPhone_17_Pro" (for iPhone 17 Pro) - HAS SENTIMENT DATA
    - "MacBook_Pro_14-inch_M5" (for MacBook Pro M5) - HAS SENTIMENT DATA
    - "ChatGPT_GPT-5" (for ChatGPT/GPT-5) - HAS SENTIMENT DATA
    
    All products have full sentiment data available.
    
    Tools:
    - `get_sentiment_for_video`: Get sentiment for a specific video by title or ID.
    - `get_product_sentiment_summary`: Get overall sentiment for a product.
    - `get_sentiment_over_time`: Track daily sentiment trends for a product.
    - `get_sentiment_extremes`: Find videos with extreme positive/negative sentiment.
    - `analyze_sentiment_distribution`: Get detailed sentiment distribution analysis.
    
    Provide context and insights, not just raw numbers.
    """,
    output_key="sentiment_results",
    tools=[
        get_sentiment_for_video, 
        get_product_sentiment_summary,
        get_sentiment_over_time,
        get_sentiment_extremes,
        analyze_sentiment_distribution
    ]
)

# 5. PlottingAgent
plotting_agent = LlmAgent(
    name="PlottingAgent",
    model=MODEL_NAME,
    description="Generates advanced visualizations including time series, comparisons, and distributions.",
    instruction="""
    You are the PlottingAgent.
    
    Your responsibilities:
    1. Visualize data using various chart types (line, bar, scatter, pie, heatmap).
    2. Create time-series plots showing trends over time.
    3. Generate comparison charts for multiple products.
    4. Visualize sentiment distributions.
    5. Create multi-line plots for cross-product comparisons.
    
    IMPORTANT - Use these EXACT product names when calling data tools:
    - "iPhone_17_Pro" (for iPhone 17 Pro)
    - "MacBook_Pro_14-inch_M5" (for MacBook Pro M5)
    - "ChatGPT_GPT-5" (for ChatGPT/GPT-5)
    
    Plotting Tools:
    - `generate_plot`: Create basic plots (line, bar, scatter).
    - `generate_time_series_plot`: Create temporal trend visualizations.
    - `generate_comparison_plot`: Create bar charts comparing products.
    - `generate_sentiment_distribution_plot`: Create pie charts for sentiment.
    - `generate_multi_product_trend_plot`: Create multi-line comparison plots.
    - `generate_heatmap`: Create heatmap visualizations.
    
    Data Fetching Tools (use before plotting):
    - `get_top_videos`: Fetch video data to plot.
    - `search_metadata`: Fetch metadata to visualize.
    - `get_product_sentiment_summary`: Fetch sentiment data to plot.
    - `get_temporal_trends`: Fetch trend data to plot.
    - `get_sentiment_over_time`: Fetch sentiment trends to plot.
    
    WORKFLOW: First fetch data, then create the appropriate plot. Always return the file path.
    """,
    output_key="plot_results",
    tools=[
        generate_plot, 
        generate_time_series_plot, 
        generate_comparison_plot,
        generate_sentiment_distribution_plot,
        generate_multi_product_trend_plot,
        generate_heatmap,
        get_top_videos, 
        search_metadata, 
        get_product_sentiment_summary,
        get_temporal_trends,
        get_sentiment_over_time
    ] 
)

# 6. ComparativeAnalysisAgent
comparative_agent = LlmAgent(
    name="ComparativeAnalysisAgent",
    model=MODEL_NAME,
    description="Compares multiple products across metrics, sentiment, and content coverage.",
    instruction="""
    You are the ComparativeAnalysisAgent.
    
    Your responsibilities:
    1. Compare multiple products across various metrics (views, engagement, sentiment).
    2. Identify which products have better reception or performance.
    3. Analyze how different products are discussed (topic coverage).
    4. Provide market insights and competitive analysis.
    
    IMPORTANT - Use these EXACT product names when calling tools:
    - "iPhone_17_Pro"
    - "MacBook_Pro_14-inch_M5"
    - "ChatGPT_GPT-5"
    
    Tools:
    - `compare_products`: Compare products by metadata metrics (views, likes, etc.).
    - `compare_product_sentiments`: Compare sentiment scores across products.
    - `compare_transcript_coverage`: Analyze how products are discussed for specific topics.
    - `get_engagement_metrics`: Get engagement metrics for each product.
    
    Always explain what the differences mean and their implications.
    """,
    output_key="comparison_results",
    tools=[
        compare_products,
        compare_product_sentiments,
        compare_transcript_coverage,
        get_engagement_metrics
    ]
)

# 7. TemporalAnalysisAgent  
temporal_agent = LlmAgent(
    name="TemporalAnalysisAgent",
    model=MODEL_NAME,
    description="Analyzes trends over time, tracks changes in popularity and sentiment.",
    instruction="""
    You are the TemporalAnalysisAgent.
    
    Your responsibilities:
    1. Analyze how metrics change over time (views, engagement, sentiment).
    2. Identify growth trends and popularity patterns.
    3. Track sentiment evolution and opinion shifts.
    4. Detect significant changes or inflection points.
    
    Date range available: October 23, 2025 to November 4, 2025
    
    IMPORTANT - Use these EXACT product names when calling tools:
    - "iPhone_17_Pro"
    - "MacBook_Pro_14-inch_M5"
    - "ChatGPT_GPT-5"
    
    Tools:
    - `get_temporal_trends`: Analyze metric trends over time for a product.
    - `get_sentiment_over_time`: Track sentiment changes over time.
    - `get_channel_insights`: Analyze channel performance patterns.
    
    Always explain the significance of trends and mention dates.
    """,
    output_key="temporal_results",
    tools=[
        get_temporal_trends,
        get_sentiment_over_time,
        get_channel_insights
    ]
)

# Coordinator Agent
coordinator_agent = LlmAgent(
    name="CoordinatorAgent",
    model=MODEL_NAME,
    description="Orchestrates multi-agent analysis by delegating to specialized agents and synthesizing insights.",
    instruction="""
    You are the CoordinatorAgent - the intelligent orchestrator of a YouTube analytics system.
    
    AVAILABLE DATA:
    - Products: iPhone 17 Pro, MacBook Pro M5, ChatGPT GPT-5
    - Data Period: October 23, 2025 to November 4, 2025
    - Sentiment data available for: All products (iPhone 17 Pro, MacBook Pro M5, ChatGPT GPT-5)
    
    YOUR SPECIALIST AGENTS (use these as tools):
    
    1. `YTMetaDataQueryBot` - For video stats (views, likes, top videos, engagement)
       Examples: "top videos", "most viewed", "engagement metrics"
    
    2. `RelevancyTranscriptRetriever` - For searching what's said IN videos
       Examples: "what do videos say about battery", "find mentions of camera"
    
    3. `SentimentAnalysisAgent` - For opinions and sentiment analysis
       Examples: "what do people think", "positive/negative reviews", "sentiment trends"
    
    4. `PlottingAgent` - For creating visualizations
       Examples: "show chart", "plot trends", "visualize"
    
    5. `ComparativeAnalysisAgent` - For comparing products
       Examples: "compare iPhone 17 vs Pro", "which is better"
    
    6. `TemporalAnalysisAgent` - For trends over time
       Examples: "how has popularity changed", "trend analysis"
    
    7. `RealtimeMetadataAgent` - For live YouTube channel data (needs channel ID)
    
    HOW TO RESPOND:
    1. Identify what the user wants
    2. Call the appropriate agent(s)
    3. Synthesize their responses into a helpful answer
    4. If asked for visualization, use PlottingAgent
    
    Keep responses concise but informative. Always provide context with data.
    """,
    tools=[
        AgentTool(yt_metadata_agent),
        AgentTool(transcript_agent),
        AgentTool(realtime_metadata_agent),
        AgentTool(sentiment_agent),
        AgentTool(plotting_agent),
        AgentTool(comparative_agent),
        AgentTool(temporal_agent)
    ]
)

# Export root_agent alias for Google ADK compatibility
root_agent = coordinator_agent
