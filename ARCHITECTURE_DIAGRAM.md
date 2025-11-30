# System Architecture Diagram

<img width="1753" height="1241" alt="ArchitectureDiagram" src="https://github.com/user-attachments/assets/963dcdea-f9a4-42bd-b2d1-c9da5b786fb1" />

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         USER QUERY INTERFACE                                 │
│                              (main.py)                                       │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      COORDINATOR AGENT                                       │
│  • Query Classification (Simple/Moderate/Complex/Analytical)                 │
│  • Multi-Agent Orchestration                                                 │
│  • Response Synthesis & Narrative Building                                   │
│  • Insight Generation                                                        │
└──────────────────┬──────────────────────────────────────────────────────────┘
                   │
                   │ Delegates to Specialized Agents
                   │
    ┌──────────────┼──────────────┬──────────────┬──────────────┐
    │              │              │              │              │
    ▼              ▼              ▼              ▼              ▼
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│  Meta   │  │ Trans   │  │ Real    │  │ Senti   │  │ Plot    │  │ Compa   │  │ Tempo   │
│  Data   │  │ Script  │  │ Time    │  │ ment    │  │ ting    │  │ rative  │  │ ral     │
│  Agent  │  │ Agent   │  │ Agent   │  │ Agent   │  │ Agent   │  │ Agent   │  │ Agent   │
└────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘
     │            │            │            │            │            │            │
     │            │            │            │            │            │            │
     └────────────┴────────────┴────────────┴────────────┴────────────┴────────────┘
                                           │
                                           ▼
                              ┌─────────────────────────┐
                              │    TOOL LAYER (24+)     │
                              └─────────────────────────┘
                                           │
        ┌──────────────────────────────────┼──────────────────────────────────┐
        │                                  │                                  │
        ▼                                  ▼                                  ▼
┌──────────────────┐          ┌──────────────────┐          ┌──────────────────┐
│  METADATA TOOLS  │          │ TRANSCRIPT TOOLS │          │ SENTIMENT TOOLS  │
│                  │          │                  │          │                  │
│ • search         │          │ • search         │          │ • get_for_video  │
│ • get_top        │          │ • multi_term     │          │ • summary        │
│ • trends ✨      │          │ • extract_topics✨│          │ • over_time ✨   │
│ • channels ✨    │          │ • coverage ✨    │          │ • extremes ✨    │
│ • compare ✨     │          │ • statistics ✨  │          │ • distribution ✨│
│ • engagement ✨  │          │                  │          │ • compare ✨     │
└──────────────────┘          └──────────────────┘          └──────────────────┘

┌──────────────────┐          ┌──────────────────┐          ┌──────────────────┐
│   PLOT TOOLS     │          │  CHANNEL TOOLS   │          │                  │
│                  │          │                  │          │                  │
│ • generate       │          │ • get_info       │          │                  │
│ • time_series ✨ │          │ • get_batch      │          │                  │
│ • comparison ✨  │          │                  │          │                  │
│ • sentiment ✨   │          │                  │          │                  │
│ • multi_trend ✨ │          │                  │          │                  │
│ • heatmap ✨     │          │                  │          │                  │
└──────────────────┘          └──────────────────┘          └──────────────────┘
        │
        └───────────────────────────────────────────────────────────────────────┐
                                                                                │
                                                                                ▼
                                                              ┌──────────────────────────┐
                                                              │     OUTPUTS              │
                                                              │ • Insights & Analysis    │
                                                              │ • Visualizations (PNG)   │
                                                              │ • Recommendations        │
                                                              └──────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                         │
│                          (Cached with LRU)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  📁 Metadata (JSON)          📁 Transcripts (JSON)    📁 Sentiment (JSON)   │
│  • iPhone 17 Pro             • iPhone 17 Pro          • iPhone 17 Pro        │
│  • MacBook Pro M5            • MacBook Pro M5         • ChatGPT GPT-5        │
│  • ChatGPT GPT-5             • ChatGPT GPT-5                                  │
│                                                                               │
│  📅 Date Range: Oct 23, 2025 - Nov 23, 2025 (31 days)                       │
└─────────────────────────────────────────────────────────────────────────────┘

Legend:
✨ = New functionality added in refinement
▼ = Data flow direction
```

---

## Agent Interaction Patterns

### Pattern 1: Simple Query
```
User Query
    ↓
Coordinator → Single Agent → Tool → Data → Response
```

### Pattern 2: Moderate Query
```
User Query
    ↓
Coordinator → Agent 1 → Tool A → Data
           ↓
           → Agent 2 → Tool B → Data
           ↓
Coordinator Synthesis → Response
```

### Pattern 3: Complex Query
```
User Query
    ↓
Coordinator → Agent 1 → Tool A → Data ──┐
           ↓                              │
           → Agent 2 → Tool B → Data ──┐ │
           ↓                            │ │
           → Agent 3 → Tool C → Data ──┤ │
           ↓                            │ │
           → Agent 4 → Tool D → Data ──┤ │
           ↓                            ↓ ↓
Coordinator Multi-Source Synthesis & Insight Generation
           ↓
     Comprehensive Response + Visualization + Recommendations
```

---

## Data Flow Example: "Compare iPhone 17 Pro and ChatGPT GPT-5 sentiment over time"

```
1. User Query
   ↓
2. Coordinator classifies as COMPLEX (comparative + temporal)
   ↓
3. Delegates to ComparativeAnalysisAgent
   ├─→ Calls compare_product_sentiments(['iPhone_17_Pro', 'ChatGPT_GPT-5'])
   │   └─→ Loads sentiment data (cached)
   │   └─→ Aggregates and ranks
   ↓
4. Delegates to TemporalAnalysisAgent  
   ├─→ Calls get_sentiment_over_time('iPhone_17_Pro')
   │   └─→ Loads sentiment data (cached)
   │   └─→ Calculates daily averages and trends
   │
   ├─→ Calls get_sentiment_over_time('ChatGPT_GPT-5')
       └─→ Uses cached data
       └─→ Calculates daily averages and trends
   ↓
5. Delegates to PlottingAgent
   ├─→ Calls generate_multi_product_trend_plot()
       └─→ Creates visualization
       └─→ Saves to plots/multi_trend_TIMESTAMP.png
   ↓
6. Coordinator synthesizes findings:
   • iPhone 17 Pro has higher average (7.8 vs 7.2)
   • ChatGPT GPT-5 showing improving trend (+0.3 over period)
   • iPhone 17 Pro stable
   • Visual chart shows clear comparison
   ↓
7. Response to user with:
   • Summary of comparison
   • Trend insights
   • Chart reference
   • Suggestion: "Would you like to see which specific features drive these differences?"
```

---

## Tool Dependency Graph

```
┌─────────────────────────────────────────────────┐
│         Core Data Loading (Cached)              │
│  • load_metadata()                              │
│  • load_transcripts()                           │
│  • load_sentiment_data()                        │
└──────────────────┬──────────────────────────────┘
                   │ Used by all tools
                   ↓
    ┌──────────────┴──────────────┬──────────────┬──────────────┐
    │                             │              │              │
┌───▼────┐              ┌─────────▼─────┐  ┌────▼────┐  ┌─────▼─────┐
│ Search │              │  Aggregation  │  │ Temporal│  │Comparative│
│ Tools  │              │     Tools     │  │  Tools  │  │   Tools   │
└────────┘              └───────────────┘  └─────────┘  └───────────┘
    │                           │              │              │
    └───────────┬───────────────┴──────────────┴──────────────┘
                │ Feed into
                ↓
    ┌──────────────────────┐
    │  Visualization Tools │
    └──────────────────────┘
```

---

## Performance Characteristics

### Cold Start (First Query)
```
Data Loading: ████████░░ 2-3s
Tool Execution: ███░░░░░░░ 0.5-1s
Agent Processing: ██░░░░░░░░ 0.3-0.5s
Total: ~3-5 seconds
```

### Warm Queries (Cached)
```
Cache Hit: ██░░░░░░░░ 0.1s
Tool Execution: ███░░░░░░░ 0.2-0.5s
Agent Processing: ██░░░░░░░░ 0.3-0.5s
Total: ~0.6-1.1 seconds
```

### Complex Multi-Agent
```
Multiple Tool Calls: ████████░░ 1-2s
Agent Coordination: ███░░░░░░░ 0.5-1s
Synthesis: ███░░░░░░░ 0.5-1s
Visualization: ████░░░░░░ 0.8-1.2s
Total: ~3-5 seconds
```

---

This architecture provides:
✅ Separation of concerns
✅ Reusable tools across agents
✅ Efficient data caching
✅ Flexible orchestration
✅ Scalable design
