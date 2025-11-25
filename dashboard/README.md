# YouTube Analytics Chatbot Dashboard

A clean, functional web interface for the multi-agent YouTube analytics system.

## Quick Start

1. **Ensure your `.env` file has the API key:**
   ```
   GOOGLE_API_KEY=your-api-key-here
   ```

2. **Run the dashboard:**
   ```bash
   cd c:\Users\Abdul\Desktop\Kaggle_Capstone
   python -m dashboard.app
   ```

3. **Open in browser:**
   ```
   http://127.0.0.1:8050
   ```

## Features

### 💬 Chat Interface
- Natural language queries about YouTube videos
- Markdown-formatted responses
- Conversation history within session

### ⚡ Quick Examples
- Pre-built example queries for common use cases
- One-click to fill the input field

### 📖 Help System
- Built-in help modal explaining capabilities
- Product availability information
- Tips for best results

## Example Queries

| Query Type | Example |
|------------|----------|
| Top Videos | "What are the top 5 most viewed iPhone 17 Pro videos?" |
| Sentiment | "What do people think about iPhone 17 Pro?" |
| Comparison | "Compare iPhone 17 Pro vs ChatGPT GPT-5 sentiment" |
| Topics | "What topics are discussed in ChatGPT GPT-5 videos?" |
| Trends | "Show me sentiment trends for iPhone 17 Pro" |
| Channels | "Which channels create the most content about MacBook Pro M5?" |

## Technical Details

- **Framework:** Dash with Bootstrap (Flatly theme)
- **Backend:** Google ADK multi-agent system
- **Agents:** 7 specialist agents coordinated by 1 orchestrator

## Troubleshooting

**"API Key not found"**
- Make sure `GOOGLE_API_KEY` is set in your `.env` file in the project root

**Slow responses**
- First query loads data into cache, subsequent queries are faster
- Complex queries involving multiple agents take longer

**No response generated**
- Try rephrasing with more specific product names
- Use exact names: "iPhone 17 Pro", "MacBook Pro", "ChatGPT GPT-5"
