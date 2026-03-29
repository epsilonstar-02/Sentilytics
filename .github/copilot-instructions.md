# YouTube Analytics Multi-Agent System - Copilot Instructions

## Project Overview

A **multi-agent YouTube analytics system** using Google ADK (Agent Development Kit) to analyze YouTube videos about tech product launches. The system orchestrates 7 specialized AI agents to provide insights on sentiment, trends, comparisons, and content analysis.

## Architecture

```
User Query → CoordinatorAgent → [Specialized Agents] → [Tool Layer] → [Data Layer]
```

### Agent Structure (`agents/chatbot/agents.py`)
- **CoordinatorAgent**: Routes queries to appropriate specialist agents
- **YTMetaDataQueryBot**: Video stats (views, likes, top videos)
- **RelevancyTranscriptRetriever**: Searches what creators *say* in videos
- **SentimentAnalysisAgent**: Opinion analysis and sentiment trends
- **PlottingAgent**: Chart generation (time series, comparisons, heatmaps)
- **ComparativeAnalysisAgent**: Cross-product comparisons
- **TemporalAnalysisAgent**: Trend analysis over time
- **RealtimeMetadataAgent**: Live YouTube channel data

### Data Flow
1. User query hits `CoordinatorAgent` which classifies and delegates
2. Specialist agents call tools from `agents/chatbot/tools/`
3. Tools read JSON data from `data_collector/data/` (cached via `@lru_cache`)
4. Plots saved to `plots/` directory

## Critical Conventions

### Product Name Normalization
**Always use exact product folder names** when calling tools:
```python
# CORRECT - matches folder names in data_collector/data/
"iPhone_17_Pro", "MacBook_Pro_14-inch_M5", "ChatGPT_GPT-5"

# WRONG - will fail or return empty results
"iPhone 17", "iphone 17 pro", "macbook"
```

All tools use `normalize_product_name()` from `agents/chatbot/tools/constants.py`.

### Data Availability
- **Metadata/Transcripts**: All 3 products (iPhone_17_Pro, MacBook_Pro_14-inch_M5, ChatGPT_GPT-5)
- **Sentiment data**: All 3 products have sentiment data
- **Date range**: October 23, 2025 - November 4, 2025

## Key File Patterns

### Adding New Tools
1. Create function in appropriate `tools/*.py` file
2. Use `@lru_cache` for data loading functions
3. Import and add to agent's `tools=[]` list in `agents.py`
4. Include product name normalization at the start

```python
# Pattern from tools/sentiment_analysis.py
def new_tool(product: str, ...) -> Dict:
    normalized = normalize_product_name(product)  # Always normalize first
    data = load_sentiment_data(normalized)        # Use cached loader
    # ... process and return
```

### Data Structure
- `data_collector/data/metadata/{product}/{date}.json` - Video metadata
- `data_collector/data/transcripts/{product}/{date}.json` - Transcripts
- `data_collector/sentiment_data/{product}/{date}.json` - Sentiment scores

JSON schema for sentiment data:
```json
{"video_id": "...", "title": "...", "sentiment_score": 0.75, "pros": [...], "cons": [...]}
```

## Running the System

```powershell
# CLI chatbot
cd agents\chatbot && python main.py

# Dash web dashboard
python -m dashboard.app  # Opens http://127.0.0.1:8050
```

### Required Environment Variables (`.env`)
```
GOOGLE_API_KEY=...    # For Google ADK agents (Gemini)
YOUTUBE_API_KEY=...   # For live channel data
NVIDIA_API_KEY=...    # For sentiment analysis (NVIDIA Llama API)
```

## Development Patterns

### Agent Instructions Pattern
When modifying agent behavior, update the `instruction=` string in `agents.py`. Include:
1. Clear responsibility list
2. **Exact product names** the agent should use
3. Available tools with descriptions
4. Output expectations

### Adding a New Agent
1. Define `LlmAgent` in `agents.py` with `model="gemini-2.5-flash"`
2. Add as `AgentTool(new_agent)` to `coordinator_agent.tools`
3. Update coordinator's instruction to describe when to use it

### Visualization Pattern (PlottingAgent)
Plots require two-step workflow: **fetch data first, then plot**
```python
# Agent must: 1) Call data tool (e.g., get_top_videos)
#            2) Pass results to plotting tool (e.g., generate_comparison_plot)
```

## Testing Queries

Test after changes using these from `QUICK_START_GUIDE.md`:
- Metadata: "What are the top 5 most viewed iPhone 17 Pro videos?"
- Transcript: "What topics are discussed in ChatGPT GPT-5 videos?"
- Sentiment: "Compare sentiment between iPhone 17 Pro and ChatGPT GPT-5"
- Temporal: "Show me sentiment trends for iPhone 17 Pro over time"
