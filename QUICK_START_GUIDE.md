# Quick Start Guide - Testing the Enhanced Agentic System

## Setup Steps

### 1. Activate Virtual Environment
```powershell
cd C:\Users\Abdul\Desktop\Kaggle_Capstone
.\.venv\Scripts\Activate.ps1
```

### 2. Install/Update Dependencies
```powershell
pip install -r agents\chatbot\requirements.txt
```

### 3. Verify Environment Variables
Ensure your `.env` file contains:
```env
GOOGLE_API_KEY=your-key-here
YOUTUBE_API_KEY=your-key-here
```

### 4. Run the Chatbot
```powershell
cd agents\chatbot
python main.py
```

---

## Test Queries by Category

### 🔍 Basic Metadata Queries
Test the enhanced metadata capabilities:

```
What are the top 5 most viewed iPhone 17 Pro videos?
```

```
Show me engagement metrics for MacBook Pro 14-inch M5
```

```
Which channels are creating the most content about iPhone 17 Pro?
```

### 📝 Transcript Analysis
Test the new transcript search features:

```
What are the most discussed topics in iPhone 17 Pro videos?
```

```
Find videos that discuss both "camera" and "battery"
```

```
Compare how "price" is discussed across all products
```

### 💭 Sentiment Analysis
Test temporal and comparative sentiment features:

```
How has sentiment for iPhone 17 Pro changed over time?
```

```
Show me the most positive and most negative reviews for ChatGPT GPT-5
```

```
Analyze the sentiment distribution for iPhone 17 Pro
```

### 📊 Comparative Analysis (NEW AGENT)
Test the new ComparativeAnalysisAgent:

```
Compare sentiment between iPhone 17 Pro and ChatGPT GPT-5
```

```
Which product has the highest engagement rate?
```

```
Compare how battery life is discussed across all products
```

### 📈 Temporal Analysis (NEW AGENT)
Test the new TemporalAnalysisAgent:

```
Show me the view count trend for iPhone 17 Pro over the past month
```

```
Is ChatGPT GPT-5 gaining or losing popularity?
```

```
What's the growth rate for MacBook Pro videos?
```

### 📉 Visualization
Test the enhanced plotting capabilities:

```
Plot sentiment trends over time for iPhone 17 Pro
```

```
Create a comparison chart of average views for all products
```

```
Show me a sentiment distribution pie chart for iPhone 17 Pro
```

### 🎯 Complex Multi-Agent Queries
Test the enhanced coordinator orchestration:

```
Give me a comprehensive analysis of iPhone 17 Pro: sentiment trends, top videos, and channel insights
```

```
Compare iPhone 17 Pro and ChatGPT GPT-5 across all dimensions: views, sentiment, engagement, and trending
```

```
What's driving the success of MacBook Pro 14-inch M5? Analyze sentiment, topics discussed, and temporal trends
```

---

## Expected Capabilities

### ✅ What the System Can Now Do:

1. **Temporal Intelligence**
   - Track metrics over 31 days
   - Calculate growth rates
   - Identify trend directions
   - Detect sentiment evolution

2. **Comparative Intelligence**
   - Compare products across metrics
   - Rank products by sentiment
   - Analyze topic coverage differences
   - Identify competitive positioning

3. **Deep Analytics**
   - Channel-level insights
   - Engagement rate calculations
   - Topic extraction from transcripts
   - Sentiment distribution analysis

4. **Advanced Visualizations**
   - Time series plots with trends
   - Multi-product comparison charts
   - Sentiment distribution pie charts
   - Multi-line trend comparisons

5. **Intelligent Orchestration**
   - Multi-agent workflows
   - Context synthesis
   - Actionable insights
   - Follow-up suggestions

---

## Verification Checklist

After running test queries, verify:

- [ ] Basic queries return detailed, contextualized responses
- [ ] Temporal queries show daily trends and growth rates
- [ ] Comparative queries rank products and explain differences
- [ ] Sentiment queries track evolution and identify extremes
- [ ] Plotting queries generate high-quality images in `plots/` folder
- [ ] Complex queries coordinate multiple agents seamlessly
- [ ] Coordinator provides insights, not just raw data
- [ ] Responses include context and interpretation

---

## Troubleshooting

### If you get import errors:
```powershell
pip install --upgrade google-adk google-genai pandas matplotlib numpy
```

### If agents don't respond:
- Check that GOOGLE_API_KEY is set in .env
- Verify the key has API access enabled
- Check console for error messages

### If plotting fails:
- Ensure the `plots/` directory is created automatically
- Check that matplotlib is installed: `pip install matplotlib`

### If data isn't found:
- Verify data files exist in `data_collector/data/`
- Check product names match exactly (case-sensitive)
- Use: "iPhone 17 Pro", "MacBook Pro 14-inch M5", "ChatGPT GPT-5"

---

## Example Session Flow

```
You: What are the top 5 iPhone 17 Pro videos by views?

Bot: [YTMetaDataQueryBot provides top videos with view counts and engagement metrics]

You: How has sentiment for these videos changed over time?

Bot: [TemporalAnalysisAgent + SentimentAnalysisAgent provide trend analysis]

You: Compare this with ChatGPT GPT-5

Bot: [ComparativeAnalysisAgent provides side-by-side comparison]

You: Show me this in a chart

Bot: [PlottingAgent creates visualization and returns file path]
```

---

## Performance Notes

- **First Query:** May take 2-5 seconds (loading data into cache)
- **Subsequent Queries:** <1 second (cached data)
- **Plotting:** 1-2 seconds per visualization
- **Complex Multi-Agent:** 3-7 seconds (multiple tool calls)

---

## Next Steps

1. Run through test queries in each category
2. Try your own custom queries
3. Verify plots are generated in `plots/` folder
4. Check that responses provide insights, not just data
5. Test edge cases and error handling

Enjoy exploring your enhanced agentic system! 🚀
