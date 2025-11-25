"""
YouTube Analytics Chatbot Dashboard
A Dash-based interface for the multi-agent YouTube analytics system.
Enhanced with thinking process display and improved user experience.
"""

import dash
from dash import html, dcc, Input, Output, State, callback, ALL
import dash_bootstrap_components as dbc
import asyncio
import os
import sys
import base64
from datetime import datetime
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from google.adk.runners import InMemoryRunner
from google.genai import types
from agents.chatbot.agents import coordinator_agent

# Custom CSS for enhanced styling
CUSTOM_CSS = """
/* Root variables for theming */
:root {
    --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    --dark-gradient: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    --card-shadow: 0 10px 40px rgba(0,0,0,0.1);
    --card-hover-shadow: 0 20px 60px rgba(0,0,0,0.15);
    --border-radius: 16px;
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Body styling */
body {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
    min-height: 100vh;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Header styling */
.header-container {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 20px;
    padding: 24px 32px;
    margin-bottom: 24px;
    box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
}

.header-title {
    color: white !important;
    font-weight: 700 !important;
    font-size: 1.8rem !important;
    text-shadow: 0 2px 10px rgba(0,0,0,0.2);
}

.header-subtitle {
    color: rgba(255,255,255,0.9) !important;
}

/* Card styling */
.card {
    border: none !important;
    border-radius: var(--border-radius) !important;
    box-shadow: var(--card-shadow) !important;
    transition: var(--transition) !important;
    overflow: hidden;
    background: white !important;
}

.card:hover {
    box-shadow: var(--card-hover-shadow) !important;
    transform: translateY(-2px);
}

.card-header {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
    border-bottom: 1px solid rgba(0,0,0,0.05) !important;
    font-weight: 600 !important;
    padding: 16px 20px !important;
}

/* Chat container */
.chat-container {
    background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%);
    border-radius: var(--border-radius);
    border: 1px solid rgba(0,0,0,0.05);
}

#chat-history {
    scrollbar-width: thin;
    scrollbar-color: #667eea #f1f1f1;
}

#chat-history::-webkit-scrollbar {
    width: 6px;
}

#chat-history::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}

#chat-history::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 10px;
}

/* Message bubbles */
.user-message {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border-radius: 20px 20px 5px 20px !important;
    color: white !important;
    padding: 16px 20px !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.bot-message {
    background: white !important;
    border-radius: 20px 20px 20px 5px !important;
    border: 1px solid rgba(0,0,0,0.05) !important;
    padding: 16px 20px !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
}

/* Input styling */
.input-group {
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border-radius: 50px !important;
    overflow: hidden;
}

.input-group .form-control {
    border: none !important;
    padding: 14px 20px !important;
    font-size: 15px !important;
}

.input-group .form-control:focus {
    box-shadow: none !important;
}

.input-group .input-group-text {
    border: none !important;
    background: white !important;
}

/* Button styling */
.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    padding: 12px 24px !important;
    font-weight: 600 !important;
    transition: var(--transition) !important;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
}

.btn-outline-primary {
    border: 2px solid #667eea !important;
    color: #667eea !important;
    font-weight: 500 !important;
    transition: var(--transition) !important;
}

.btn-outline-primary:hover {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border-color: transparent !important;
}

/* Badge styling */
.badge {
    font-weight: 500 !important;
    padding: 8px 12px !important;
    border-radius: 20px !important;
}

/* Accordion styling */
.accordion-item {
    border: none !important;
    border-radius: var(--border-radius) !important;
    margin-bottom: 8px;
    overflow: hidden;
}

.accordion-button {
    background: #f8f9fa !important;
    font-weight: 500 !important;
}

.accordion-button:not(.collapsed) {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
}

/* Tab styling */
.nav-tabs {
    border-bottom: none !important;
}

.nav-tabs .nav-link {
    border: none !important;
    border-radius: 20px !important;
    margin: 2px !important;
    padding: 8px 16px !important;
    font-size: 13px !important;
    transition: var(--transition) !important;
}

.nav-tabs .nav-link.active {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
}

/* Status indicator */
.status-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
    animation: pulse 2s infinite;
}

.status-dot.online {
    background: #28a745;
    box-shadow: 0 0 10px rgba(40, 167, 69, 0.5);
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

/* Product chips */
.product-chip {
    display: inline-flex;
    align-items: center;
    padding: 10px 16px;
    border-radius: 25px;
    margin: 4px;
    cursor: pointer;
    font-weight: 500;
    transition: var(--transition);
    border: 2px solid transparent;
}

.product-chip:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.product-chip.iphone {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
    color: #1565c0;
}

.product-chip.macbook {
    background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
    color: #7b1fa2;
}

.product-chip.chatgpt {
    background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
    color: #2e7d32;
}

/* Capability cards */
.capability-card {
    border-radius: 12px !important;
    padding: 16px !important;
    text-align: center;
    transition: var(--transition);
    cursor: pointer;
    background: white;
    border: 1px solid rgba(0,0,0,0.05) !important;
}

.capability-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}

/* Thinking panel */
.thinking-panel {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: var(--border-radius);
    padding: 20px;
    margin-bottom: 16px;
    color: white;
    animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Modal styling */
.modal-content {
    border: none !important;
    border-radius: 20px !important;
    box-shadow: 0 25px 80px rgba(0,0,0,0.2) !important;
}

.modal-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 20px 20px 0 0 !important;
    border: none !important;
}

.modal-header .btn-close {
    filter: brightness(0) invert(1);
}

/* Stats cards */
.stat-card {
    text-align: center;
    padding: 16px;
    border-radius: 12px;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    transition: var(--transition);
}

.stat-card:hover {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.stat-card:hover .stat-number {
    color: white !important;
}

.stat-number {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* Smooth scrolling */
* {
    scroll-behavior: smooth;
}

/* Loading animation */
.loading-dots::after {
    content: '';
    animation: dots 1.5s steps(4, end) infinite;
}

@keyframes dots {
    0%, 20% { content: ''; }
    40% { content: '.'; }
    60% { content: '..'; }
    80%, 100% { content: '...'; }
}

/* Custom dcc.Loading styles */
._dash-loading {
    position: absolute !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
}

._dash-loading-callback {
    background-color: rgba(255, 255, 255, 0.85) !important;
    backdrop-filter: blur(4px) !important;
}

/* Loading overlay message */
.loading-overlay-content {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    z-index: 1000;
}

/* Typing indicator animation */
.typing-indicator {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 12px 16px;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
    border-radius: 18px;
    border: 1px dashed rgba(102, 126, 234, 0.3);
}

.typing-indicator span {
    width: 8px;
    height: 8px;
    background: #667eea;
    border-radius: 50%;
    animation: typing-bounce 1.4s ease-in-out infinite;
}

.typing-indicator span:nth-child(1) { animation-delay: 0s; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing-bounce {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
    30% { transform: translateY(-8px); opacity: 1; }
}

/* Send button loading state */
.btn-primary:disabled {
    background: linear-gradient(135deg, #a0aee8 0%, #b89bc7 100%) !important;
    cursor: wait;
}
"""

# Initialize the app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.FLATLY,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
    ],
    title="YouTube Analytics Chatbot",
    suppress_callback_exceptions=True
)

# Inject custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>''' + CUSTOM_CSS + '''</style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Global runner and session (initialized on first use)
runner = None
session = None

# Available products with details
PRODUCTS = {
    "iPhone_17_Pro": {"name": "iPhone 17 Pro", "icon": "📱", "has_sentiment": True, "color_class": "iphone"},
    "MacBook_Pro_14-inch_M5": {"name": "MacBook Pro M5", "icon": "💻", "has_sentiment": True, "color_class": "macbook"},
    "ChatGPT_GPT-5": {"name": "ChatGPT GPT-5", "icon": "🤖", "has_sentiment": True, "color_class": "chatgpt"},
}

# Categorized example queries
EXAMPLE_CATEGORIES = {
    "📊 Video Stats": {
        "description": "Find top performing videos and engagement metrics",
        "examples": [
            {"query": "What are the top 5 most viewed iPhone 17 Pro videos?", "description": "Top videos by views"},
            {"query": "Show me the most liked MacBook Pro M5 videos", "description": "Top videos by likes"},
            {"query": "Which channels create the most iPhone 17 Pro content?", "description": "Channel analysis"},
        ]
    },
    "🔍 Transcript Search": {
        "description": "Search what creators say IN their videos",
        "examples": [
            {"query": "What do videos say about iPhone 17 Pro battery life?", "description": "Search for battery mentions"},
            {"query": "Find videos discussing ChatGPT code generation", "description": "Topic search"},
            {"query": "What topics are most discussed in MacBook Pro M5 videos?", "description": "Topic extraction"},
        ]
    },
    "💭 Sentiment Analysis": {
        "description": "Understand public opinion and reviews",
        "examples": [
            {"query": "What do people think about iPhone 17 Pro?", "description": "Overall sentiment"},
            {"query": "What are the pros and cons mentioned for ChatGPT GPT-5?", "description": "Pros/Cons analysis"},
            {"query": "Show me the most positive iPhone 17 Pro reviews", "description": "Sentiment extremes"},
        ]
    },
    "⚖️ Comparisons": {
        "description": "Compare products head-to-head",
        "examples": [
            {"query": "Compare iPhone 17 Pro vs MacBook Pro M5", "description": "Product comparison"},
            {"query": "How does iPhone 17 Pro sentiment compare to ChatGPT?", "description": "Cross-product sentiment"},
        ]
    },
    "📈 Trends": {
        "description": "Track changes over time",
        "examples": [
            {"query": "Show me sentiment trends for iPhone 17 Pro over time", "description": "Sentiment timeline"},
            {"query": "How has iPhone 17 Pro coverage changed?", "description": "Coverage trends"},
        ]
    },
}

# Help content with enhanced formatting
HELP_CONTENT = """
## 🎯 What Can This Chatbot Do?

This AI-powered chatbot analyzes YouTube videos about tech products using a **multi-agent system** with 7 specialized AI agents.

### 🤖 The Agent Team

| Agent | Specialty | Use For |
|-------|-----------|---------|
| **YTMetaDataQueryBot** | Video statistics | Views, likes, top videos |
| **RelevancyTranscriptRetriever** | Content search | What creators say |
| **SentimentAnalysisAgent** | Opinion analysis | Reviews, sentiment |
| **PlottingAgent** | Visualization | Charts, trends |
| **ComparativeAnalysisAgent** | Comparisons | Product vs product |
| **TemporalAnalysisAgent** | Time analysis | Trends over time |
| **RealtimeMetadataAgent** | Live data | Channel info |

---

### 📦 Available Products

| Product | Data Available | Sentiment |
|---------|---------------|-----------|
| iPhone 17 Pro | ✅ Metadata, Transcripts | ✅ Yes |
| MacBook Pro M5 | ✅ Metadata, Transcripts | ✅ Yes |
| ChatGPT GPT-5 | ✅ Metadata, Transcripts | ✅ Yes |

**Data Period:** October 23 - November 4, 2025

---

### 💡 Tips for Best Results

1. **Be specific** - "Top 5 iPhone 17 Pro videos" works better than "show videos"
2. **Name products clearly** - Use exact names like "iPhone 17 Pro", "MacBook Pro M5"
3. **Ask one thing at a time** - Complex queries work, but simple ones are faster
4. **Use follow-up suggestions** - Click the suggested questions after each response

---

### 🔄 Understanding the Thinking Process

When you ask a question, you'll see a **"Thinking..."** panel showing:
- 🧠 Which agents are being consulted
- 🔧 Which tools are being used
- 📊 What data is being analyzed

This helps you understand how the AI arrives at its answer!
"""


def create_thinking_panel(thinking_steps=None, is_active=False):
    """Create the thinking process panel."""
    if not is_active:
        return html.Div(id="thinking-container", style={"display": "none"})
    
    steps = thinking_steps or []
    
    return html.Div([
        html.Div([
            html.Div([
                html.I(className="fas fa-brain me-2"),
                html.Strong("AI Thinking Process"),
                dbc.Spinner(size="sm", color="light", type="grow", className="ms-2"),
            ], className="d-flex align-items-center mb-2"),
            html.Div([
                html.Div([
                    html.Span(step.get("icon", "🔄"), className="me-2"),
                    html.Span(step.get("agent", ""), style={
                        "background": "rgba(255,255,255,0.2)",
                        "padding": "3px 8px",
                        "borderRadius": "12px",
                        "fontSize": "12px",
                        "marginRight": "5px"
                    }),
                    html.Span(step.get("action", "Processing...")),
                ], style={
                    "background": "rgba(255,255,255,0.1)",
                    "borderRadius": "5px",
                    "padding": "8px 12px",
                    "margin": "5px 0",
                    "fontSize": "14px"
                })
                for step in steps
            ] if steps else [
                html.Div([
                    html.Span("🔄", className="me-2"),
                    html.Span("Analyzing your request..."),
                ], style={
                    "background": "rgba(255,255,255,0.1)",
                    "borderRadius": "5px",
                    "padding": "8px 12px",
                    "margin": "5px 0",
                    "fontSize": "14px"
                })
            ], id="thinking-steps")
        ], style={
            "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "borderRadius": "10px",
            "padding": "15px",
            "marginBottom": "15px",
            "color": "white"
        })
    ], id="thinking-container")


def parse_response_for_images(response: str):
    """
    Parse response text to extract base64 images and/or load images from file paths.
    Returns tuple of (cleaned_text, list_of_base64_images)
    """
    import re
    
    images = []
    cleaned_text = response
    
    # Extract base64 images from [IMAGE_BASE64:...] markers
    base64_pattern = r'\[IMAGE_BASE64:([A-Za-z0-9+/=]+)\]'
    matches = re.findall(base64_pattern, response)
    
    for match in matches:
        images.append(match)
    
    # Remove the IMAGE_BASE64 markers from text
    cleaned_text = re.sub(base64_pattern, '', cleaned_text)
    
    # Also try to find and load images from file paths if no base64 found
    if not images:
        # Look for plot file paths in the response - use a single comprehensive pattern
        # Match both Windows paths (C:\...\plots\...) and Linux paths (/workspace/plots/...)
        windows_pattern = r'C:[\\\/][^\s\n]*[\\\/]plots[\\\/][^\s\n]+\.png'
        linux_pattern = r'\/[^\s\n]*\/plots\/[^\s\n]+\.png'
        
        path_matches = re.findall(windows_pattern, response, re.IGNORECASE)
        path_matches.extend(re.findall(linux_pattern, response, re.IGNORECASE))
        
        # Deduplicate paths (normalize and use set)
        seen_paths = set()
        for path_match in path_matches:
            # Normalize the path based on current OS
            img_path = os.path.normpath(path_match.replace('\\\\', os.sep).replace('/', os.sep).replace('\\', os.sep))
            
            # Skip if we've already processed this path
            if img_path.lower() in seen_paths:
                continue
            seen_paths.add(img_path.lower())
            
            # Try to load the image and convert to base64
            try:
                if os.path.exists(img_path):
                    with open(img_path, 'rb') as img_file:
                        img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                        images.append(img_base64)
            except Exception as e:
                print(f"Could not load image from {path_match}: {e}")
    
    # Also clean up markdown image references to local files
    cleaned_text = re.sub(r'!\[Plot\]\([^)]+\)\n*', '', cleaned_text)
    
    # Clean up extra newlines
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text).strip()
    
    return cleaned_text, images


def create_response_with_images(response: str):
    """
    Create Dash components for response with inline images.
    """
    cleaned_text, images = parse_response_for_images(response)
    
    components = []
    
    # Add the text content
    if cleaned_text:
        components.append(dcc.Markdown(cleaned_text, className="mb-3"))
    
    # Add images if any
    for i, img_base64 in enumerate(images):
        components.append(
            html.Div([
                html.Img(
                    src=f"data:image/png;base64,{img_base64}",
                    style={
                        "maxWidth": "100%",
                        "borderRadius": "8px",
                        "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
                        "marginBottom": "10px"
                    }
                )
            ], className="text-center mb-3")
        )
    
    return html.Div(components) if components else dcc.Markdown(response, className="mb-0")


def create_suggestion_buttons(suggestions):
    """Create follow-up suggestion buttons."""
    if not suggestions:
        return html.Div()
    
    return html.Div([
        html.Hr(className="my-3"),
        html.Small([
            html.I(className="fas fa-lightbulb me-1 text-warning"),
            "Try asking:"
        ], className="text-muted d-block mb-2"),
        html.Div([
            dbc.Button(
                [html.I(className="fas fa-arrow-right me-1"), suggestion],
                id={"type": "suggestion-btn", "index": i},
                color="outline-primary",
                size="sm",
                className="me-2 mb-2",
                style={"fontSize": "12px", "borderRadius": "15px"}
            )
            for i, suggestion in enumerate(suggestions)
        ])
    ], className="mt-3")


def create_product_selector():
    """Create the product selector component with enhanced styling."""
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.I(className="fas fa-cube me-2", style={"color": "#667eea"}),
                html.Span("Products", className="fw-bold"),
            ], className="d-flex align-items-center"),
        ], className="py-3"),
        dbc.CardBody([
            html.P("Click to start a conversation:", className="text-muted small mb-3"),
            html.Div([
                html.Div([
                    html.Span(info["icon"], style={"fontSize": "1.2rem"}),
                    html.Span(info["name"], className="ms-2 fw-medium"),
                    dbc.Badge("✓", color="success", pill=True, className="ms-2") if info["has_sentiment"] else None
                ], 
                id={"type": "product-chip", "index": pid},
                className=f"product-chip {info.get('color_class', '')}")
                for pid, info in PRODUCTS.items()
            ], className="d-flex flex-column gap-2"),
            html.Div([
                html.I(className="fas fa-check-circle me-1 text-success"),
                html.Small("All products have sentiment analysis", className="text-muted")
            ], className="mt-3 pt-2 border-top")
        ], className="py-3"),
    ], className="mb-3")


def create_capability_cards():
    """Create interactive capability cards with enhanced styling."""
    capabilities = [
        {"icon": "fas fa-chart-bar", "name": "📊 Video Stats", "color": "primary", "gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
         "desc": "Views, likes, top videos", "example": "Top 5 most viewed iPhone 17 Pro videos"},
        {"icon": "fas fa-search", "name": "🔍 Transcripts", "color": "info", "gradient": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
         "desc": "Search what creators say", "example": "What do videos say about battery?"},
        {"icon": "fas fa-heart", "name": "💭 Sentiment", "color": "success", "gradient": "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
         "desc": "Public opinion analysis", "example": "What do people think about iPhone 17 Pro?"},
        {"icon": "fas fa-chart-line", "name": "📈 Trends", "color": "warning", "gradient": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
         "desc": "Track changes over time", "example": "Show sentiment trends for iPhone 17 Pro"},
        {"icon": "fas fa-balance-scale", "name": "⚖️ Compare", "color": "danger", "gradient": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
         "desc": "Compare products", "example": "Compare iPhone 17 Pro vs MacBook Pro M5"},
        {"icon": "fas fa-image", "name": "📉 Charts", "color": "secondary", "gradient": "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
         "desc": "Generate visualizations", "example": "Plot iPhone 17 Pro sentiment over time"},
    ]
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div([
                        html.Div([
                            html.Span(cap["name"].split()[0], style={"fontSize": "1.5rem"}),
                        ], className="mb-2"),
                        html.Div(cap["name"].split(maxsplit=1)[1] if len(cap["name"].split()) > 1 else "", 
                                className="fw-semibold mb-1", style={"fontSize": "0.85rem"}),
                        html.Small(cap["desc"], className="text-muted"),
                    ], className="capability-card p-3")
                ],
                id={"type": "capability-card", "index": i},
                n_clicks=0)
            ], width=6)
            for i, cap in enumerate(capabilities)
        ])
    ])


def create_onboarding_modal():
    """Create the onboarding/welcome modal for first-time users."""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H4([
                html.Span("👋", className="me-2"),
                "Welcome to YouTube Analytics Chatbot!"
            ], className="mb-0")
        ]),
        dbc.ModalBody([
            # Step 1
            html.Div([
                html.Div([
                    html.Span("1", style={
                        "width": "30px",
                        "height": "30px",
                        "borderRadius": "50%",
                        "display": "inline-flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "fontWeight": "bold",
                        "marginRight": "10px",
                        "background": "#667eea",
                        "color": "white"
                    }),
                    html.Strong("Meet Your AI Team")
                ], className="d-flex align-items-center mb-3"),
                html.P([
                    "This chatbot uses ", html.Strong("7 specialized AI agents"),
                    " that work together to analyze YouTube videos about tech products."
                ]),
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Span("🔍", className="me-2"),
                            html.Small("Search videos & transcripts")
                        ], className="p-2 bg-light rounded mb-2"),
                        html.Div([
                            html.Span("💭", className="me-2"),
                            html.Small("Analyze sentiment & opinions")
                        ], className="p-2 bg-light rounded mb-2"),
                    ], width=6),
                    dbc.Col([
                        html.Div([
                            html.Span("📊", className="me-2"),
                            html.Small("Get stats & metrics")
                        ], className="p-2 bg-light rounded mb-2"),
                        html.Div([
                            html.Span("📈", className="me-2"),
                            html.Small("Track trends & compare")
                        ], className="p-2 bg-light rounded mb-2"),
                    ], width=6),
                ], className="mb-3"),
            ]),
            
            html.Hr(),
            
            # Step 2
            html.Div([
                html.Div([
                    html.Span("2", style={
                        "width": "30px",
                        "height": "30px",
                        "borderRadius": "50%",
                        "display": "inline-flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "fontWeight": "bold",
                        "marginRight": "10px",
                        "background": "#667eea",
                        "color": "white"
                    }),
                    html.Strong("Available Products")
                ], className="d-flex align-items-center mb-3"),
                html.P("Ask questions about these tech products:"),
                html.Div([
                    dbc.Badge([html.Span("📱 "), "iPhone 17 Pro"], color="primary", className="me-2 p-2"),
                    dbc.Badge([html.Span("💻 "), "MacBook Pro M5"], color="info", className="me-2 p-2"),
                    dbc.Badge([html.Span("🤖 "), "ChatGPT GPT-5"], color="success", className="me-2 p-2"),
                ], className="mb-2"),
                html.Small("📅 Data: October 23 - November 4, 2025", className="text-muted d-block mt-2"),
            ]),
            
            html.Hr(),
            
            # Step 3
            html.Div([
                html.Div([
                    html.Span("3", style={
                        "width": "30px",
                        "height": "30px",
                        "borderRadius": "50%",
                        "display": "inline-flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "fontWeight": "bold",
                        "marginRight": "10px",
                        "background": "#667eea",
                        "color": "white"
                    }),
                    html.Strong("Try These Examples")
                ], className="d-flex align-items-center mb-3"),
                html.Div([
                    html.Div([
                        html.Code("What are the top 5 most viewed iPhone 17 Pro videos?", 
                                 className="d-block p-2 bg-light rounded mb-2"),
                        html.Code("What do people think about ChatGPT GPT-5?", 
                                 className="d-block p-2 bg-light rounded mb-2"),
                        html.Code("Compare iPhone 17 Pro vs MacBook Pro M5", 
                                 className="d-block p-2 bg-light rounded"),
                    ])
                ]),
            ]),
            
            html.Hr(),
            
            # Pro Tip
            html.Div([
                html.Div([
                    html.I(className="fas fa-lightbulb text-warning me-2"),
                    html.Strong("Pro Tip:", className="text-warning"),
                ], className="mb-2"),
                html.P([
                    "Watch the ", html.Strong("'Thinking Process'"), 
                    " panel to see how the AI agents work together to answer your questions!"
                ], className="mb-0"),
            ], className="bg-light p-3 rounded"),
        ]),
        dbc.ModalFooter([
            dbc.Button([
                html.I(className="fas fa-rocket me-2"),
                "Let's Get Started!"
            ], id="close-onboarding", color="primary", size="lg", style={
                "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "border": "none",
                "borderRadius": "25px",
                "padding": "12px 32px"
            })
        ])
    ], id="onboarding-modal", is_open=True, size="lg", centered=True)


# Layout
app.layout = dbc.Container([
    # Onboarding Modal
    create_onboarding_modal(),
    
    # Header with enhanced styling
    html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Span("🎬", style={"fontSize": "2rem", "marginRight": "12px"}),
                    html.Span("YouTube Analytics", className="header-title"),
                ], className="d-flex align-items-center"),
                html.P([
                    html.I(className="fas fa-robot me-2"),
                    "AI-powered insights from YouTube tech reviews • ",
                    html.Span("7 specialized agents", style={"fontWeight": "600"})
                ], className="header-subtitle mb-0 mt-1"),
            ], width=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-question-circle me-1"),
                        "Help"
                    ], id="help-button", outline=True, color="light", size="sm", 
                       style={"borderRadius": "20px", "border": "2px solid rgba(255,255,255,0.5)"}),
                    dbc.Button([
                        html.I(className="fas fa-plus me-1"),
                        "New Chat"
                    ], id="reset-button", outline=True, color="light", size="sm",
                       style={"borderRadius": "20px", "border": "2px solid rgba(255,255,255,0.5)"}),
                ], className="float-end"),
            ], width=4, className="d-flex align-items-center justify-content-end"),
        ]),
    ], className="header-container"),
    
    # Main content row
    dbc.Row([
        # Chat column
        dbc.Col([
            # Thinking Panel (shown during processing)
            html.Div(id="thinking-display"),
            
            # Chat history container with enhanced styling
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-comments me-2", style={"color": "#667eea"}),
                            html.Span("Conversation", className="fw-bold"),
                        ], className="d-flex align-items-center"),
                        dbc.Badge([
                            html.I(className="fas fa-bolt me-1"),
                            "AI Powered"
                        ], color="success", pill=True, style={"fontSize": "11px"}),
                    ], className="d-flex align-items-center justify-content-between w-100"),
                ]),
                dbc.CardBody([
                    # Chat messages area with loading indicator
                    dcc.Loading(
                        id="chat-loading",
                        type="default",
                        color="#667eea",
                        children=[
                            html.Div(
                                id="chat-history",
                                children=[
                                    # Welcome message with enhanced styling
                                    html.Div([
                                        html.Div([
                                            html.Div([
                                                html.Div([
                                                    html.Img(src="https://api.dicebear.com/7.x/bottts/svg?seed=assistant&backgroundColor=667eea", 
                                                            style={"width": "32px", "height": "32px", "borderRadius": "50%"}),
                                                    html.Strong("Assistant", className="ms-2"),
                                                ], className="d-flex align-items-center"),
                                            ], className="mb-3"),
                                            html.P([
                                                "👋 Hello! I'm your ", html.Strong("YouTube Analytics Assistant"), ".",
                                            ], className="mb-2"),
                                            html.P([
                                                "I can help you analyze videos about:"
                                            ], className="mb-2"),
                                            html.Div([
                                                dbc.Badge([html.Span("📱 "), "iPhone 17 Pro"], color="primary", pill=True, className="me-2 mb-1"),
                                                dbc.Badge([html.Span("💻 "), "MacBook Pro M5"], pill=True, className="me-2 mb-1", 
                                                         style={"background": "linear-gradient(135deg, #a855f7 0%, #6366f1 100%)"}),
                                                dbc.Badge([html.Span("🤖 "), "ChatGPT GPT-5"], color="success", pill=True, className="mb-1"),
                                            ], className="mb-3"),
                                            html.Div([
                                                html.I(className="fas fa-lightbulb text-warning me-2"),
                                                html.Span("Click an example below or type your own question!", className="text-muted"),
                                            ], className="small p-2 rounded", style={"background": "rgba(255, 193, 7, 0.1)"}),
                                        ], className="bot-message"),
                                    ], className="mb-3"),
                                ],
                                style={
                                    "height": "400px",
                                    "overflowY": "auto",
                                    "padding": "16px",
                                }
                            ),
                        ],
                        # Custom loading spinner with overlay
                        parent_style={"position": "relative"},
                        overlay_style={"visibility": "visible", "opacity": 0.6, "backgroundColor": "white"},
                    ),
                ]),
                dbc.CardFooter([
                    # Enhanced input area
                    dbc.InputGroup([
                        dbc.InputGroupText(
                            html.I(className="fas fa-comment-dots", style={"color": "#667eea"}),
                            style={"background": "white", "border": "none", "paddingLeft": "20px"}
                        ),
                        dbc.Input(
                            id="user-input",
                            placeholder="Ask about YouTube videos... (e.g., 'Top iPhone 17 Pro videos')",
                            type="text",
                            style={"border": "none", "fontSize": "15px"}
                        ),
                        dbc.Button([
                            html.I(className="fas fa-paper-plane")
                        ], id="send-button", color="primary", style={
                            "borderRadius": "0 50px 50px 0",
                            "padding": "12px 24px",
                            "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                            "border": "none"
                        }),
                    ], style={"borderRadius": "50px", "overflow": "hidden", "border": "2px solid #e9ecef"}),
                    # Loading indicator
                    html.Div(id="loading-output", className="mt-2"),
                ], style={"background": "transparent", "border": "none", "padding": "20px"}),
            ], className="chat-container"),
            
            # Example queries by category with enhanced styling
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.I(className="fas fa-bolt me-2", style={"color": "#f59e0b"}),
                        html.Span("Quick Examples", className="fw-bold"),
                    ], className="d-flex align-items-center"),
                    dbc.Button(
                        html.I(className="fas fa-chevron-down"),
                        id="toggle-examples",
                        color="link",
                        size="sm",
                        className="float-end p-0",
                        style={"color": "#667eea"}
                    )
                ], className="py-3 d-flex justify-content-between align-items-center"),
                dbc.Collapse([
                    dbc.CardBody([
                        dbc.Tabs([
                            dbc.Tab([
                                html.Div([
                                    html.P(cat_info["description"], className="text-muted small mt-2"),
                                    html.Div([
                                        dbc.Button([
                                            html.Small(ex["description"]),
                                        ],
                                        id={"type": "example-btn", "category": cat_name, "index": i},
                                        color="outline-secondary",
                                        size="sm",
                                        className="me-2 mb-2",
                                        style={"fontSize": "11px", "borderRadius": "15px"},
                                        title=ex["query"])
                                        for i, ex in enumerate(cat_info["examples"])
                                    ])
                                ], className="p-2")
                            ], label=cat_name, tab_id=cat_name)
                            for cat_name, cat_info in EXAMPLE_CATEGORIES.items()
                        ], id="example-tabs", active_tab="📊 Video Stats")
                    ], className="py-2"),
                ], id="examples-collapse", is_open=True),
            ], className="mt-3"),
            
        ], width=8),
        
        # Sidebar column with enhanced styling
        dbc.Col([
            # Status card with modern design
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.I(className="fas fa-satellite-dish me-2", style={"color": "#10b981"}),
                        html.Span("System Status", className="fw-bold"),
                    ], className="d-flex align-items-center"),
                ], className="py-3"),
                dbc.CardBody([
                    html.Div([
                        html.Span(className="status-dot online me-2"),
                        html.Span("All Systems Operational", className="text-success fw-medium"),
                    ], id="api-status", className="d-flex align-items-center mb-3"),
                    html.Hr(className="my-3"),
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Div("3", className="stat-number"),
                                html.Small("Products", className="d-block text-muted fw-medium")
                            ], className="stat-card")
                        ], width=4),
                        dbc.Col([
                            html.Div([
                                html.Div("7", className="stat-number"),
                                html.Small("Agents", className="d-block text-muted fw-medium")
                            ], className="stat-card")
                        ], width=4),
                        dbc.Col([
                            html.Div([
                                html.Div("24+", className="stat-number"),
                                html.Small("Tools", className="d-block text-muted fw-medium")
                            ], className="stat-card")
                        ], width=4),
                    ], className="g-2"),
                ], className="py-3"),
            ], className="mb-3"),
            
            # Product selector
            create_product_selector(),
            
            # Capabilities card with enhanced styling
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.I(className="fas fa-magic me-2", style={"color": "#8b5cf6"}),
                        html.Span("Capabilities", className="fw-bold"),
                    ], className="d-flex align-items-center"),
                ], className="py-3"),
                dbc.CardBody([
                    create_capability_cards()
                ], className="py-3"),
            ], className="mb-3"),
            
            # Session info with enhanced styling
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.I(className="fas fa-chart-line me-2", style={"color": "#06b6d4"}),
                        html.Span("Session", className="fw-bold"),
                    ], className="d-flex align-items-center"),
                ], className="py-3"),
                dbc.CardBody([
                    html.Div(id="session-info", children=[
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-comment-alt me-2", style={"color": "#667eea"}),
                                html.Span("Messages", className="text-muted small"),
                            ], className="d-flex align-items-center"),
                            html.Strong("0", className="ms-auto", style={"color": "#667eea"}),
                        ], className="d-flex align-items-center justify-content-between mb-2 p-2 rounded", 
                           style={"background": "rgba(102, 126, 234, 0.1)"}),
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-clock me-2", style={"color": "#10b981"}),
                                html.Span("Started", className="text-muted small"),
                            ], className="d-flex align-items-center"),
                            html.Strong(f"{datetime.now().strftime('%H:%M')}", className="ms-auto", style={"color": "#10b981"}),
                        ], className="d-flex align-items-center justify-content-between p-2 rounded",
                           style={"background": "rgba(16, 185, 129, 0.1)"}),
                    ]),
                ], className="py-3"),
            ]),
            
        ], width=4),
    ]),
    
    # Help Modal with enhanced styling
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle([
            html.I(className="fas fa-book-open me-2"),
            "How to Use This Chatbot"
        ]), style={"border": "none"}),
        dbc.ModalBody([
            dcc.Markdown(HELP_CONTENT)
        ], style={"padding": "24px"}),
        dbc.ModalFooter(
            dbc.Button([
                html.I(className="fas fa-check me-1"),
                "Got it!"
            ], id="close-help", className="ms-auto", color="primary"),
            style={"border": "none"}
        ),
    ], id="help-modal", size="lg", scrollable=True),
    
    # Store for chat history and state
    dcc.Store(id="chat-store", data=[]),
    dcc.Store(id="message-count", data=0),
    dcc.Store(id="current-suggestions", data=[]),
    dcc.Store(id="selected-product", data=None),
    dcc.Store(id="thinking-steps-store", data=[]),
    
], fluid=True, className="py-4", style={"maxWidth": "1440px"})


# Callback to toggle help modal
@callback(
    Output("help-modal", "is_open"),
    [Input("help-button", "n_clicks"), Input("close-help", "n_clicks")],
    [State("help-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_help_modal(n1, n2, is_open):
    return not is_open


# Callback to close onboarding modal
@callback(
    Output("onboarding-modal", "is_open"),
    Input("close-onboarding", "n_clicks"),
    prevent_initial_call=True
)
def close_onboarding(n_clicks):
    return False


# Callback to toggle examples collapse
@callback(
    Output("examples-collapse", "is_open"),
    Input("toggle-examples", "n_clicks"),
    State("examples-collapse", "is_open"),
    prevent_initial_call=True
)
def toggle_examples(n_clicks, is_open):
    return not is_open


# Callback to handle example button clicks
@callback(
    Output("user-input", "value"),
    [Input({"type": "example-btn", "category": ALL, "index": ALL}, "n_clicks"),
     Input({"type": "suggestion-btn", "index": ALL}, "n_clicks"),
     Input({"type": "product-chip", "index": ALL}, "n_clicks"),
     Input({"type": "capability-card", "index": ALL}, "n_clicks")],
    [State("current-suggestions", "data")],
    prevent_initial_call=True
)
def handle_quick_actions(example_clicks, suggestion_clicks, product_clicks, capability_clicks, current_suggestions):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    triggered_id = ctx.triggered[0]["prop_id"]
    
    # Handle example buttons
    if "example-btn" in triggered_id:
        button_info = json.loads(triggered_id.split(".")[0])
        category = button_info["category"]
        index = button_info["index"]
        return EXAMPLE_CATEGORIES[category]["examples"][index]["query"]
    
    # Handle suggestion buttons
    if "suggestion-btn" in triggered_id:
        button_info = json.loads(triggered_id.split(".")[0])
        index = button_info["index"]
        if current_suggestions and index < len(current_suggestions):
            return current_suggestions[index]
        return dash.no_update
    
    # Handle product chip clicks
    if "product-chip" in triggered_id:
        button_info = json.loads(triggered_id.split(".")[0])
        product_id = button_info["index"]
        product_name = PRODUCTS[product_id]["name"]
        return f"Tell me about {product_name} videos"
    
    # Handle capability card clicks
    if "capability-card" in triggered_id:
        button_info = json.loads(triggered_id.split(".")[0])
        index = button_info["index"]
        examples = [
            "What are the top 5 most viewed iPhone 17 Pro videos?",
            "What do videos say about iPhone 17 Pro battery life?",
            "What do people think about iPhone 17 Pro?",
            "Show me sentiment trends for iPhone 17 Pro over time",
            "Compare iPhone 17 Pro vs MacBook Pro M5",
            "Generate a chart showing iPhone 17 Pro sentiment distribution"
        ]
        if index < len(examples):
            return examples[index]
    
    return dash.no_update


# Callback to reset chat
@callback(
    [Output("chat-history", "children", allow_duplicate=True),
     Output("chat-store", "data", allow_duplicate=True),
     Output("message-count", "data", allow_duplicate=True)],
    Input("reset-button", "n_clicks"),
    prevent_initial_call=True
)
def reset_chat(n_clicks):
    """Reset chat with enhanced welcome message."""
    welcome_msg = html.Div([
        html.Div([
            html.Div([
                html.Img(src="https://api.dicebear.com/7.x/bottts/svg?seed=assistant&backgroundColor=667eea", 
                        style={"width": "32px", "height": "32px", "borderRadius": "50%"}),
                html.Strong("Assistant", className="ms-2"),
            ], className="d-flex align-items-center mb-3"),
            html.P([
                "👋 Hello! I'm your ", html.Strong("YouTube Analytics Assistant"), ".",
            ], className="mb-2"),
            html.P("I can help you analyze videos about:", className="mb-2"),
            html.Div([
                dbc.Badge([html.Span("📱 "), "iPhone 17 Pro"], color="primary", pill=True, className="me-2 mb-1"),
                dbc.Badge([html.Span("💻 "), "MacBook Pro M5"], pill=True, className="me-2 mb-1", 
                         style={"background": "linear-gradient(135deg, #a855f7 0%, #6366f1 100%)"}),
                dbc.Badge([html.Span("🤖 "), "ChatGPT GPT-5"], color="success", pill=True, className="mb-1"),
            ], className="mb-3"),
            html.Div([
                html.I(className="fas fa-lightbulb text-warning me-2"),
                html.Span("Click an example below or type your own question!", className="text-muted"),
            ], className="small p-2 rounded", style={"background": "rgba(255, 193, 7, 0.1)"}),
        ], className="bot-message"),
    ], className="mb-3")
    
    return [welcome_msg], [], 0


# Main chat callback
@callback(
    [Output("chat-history", "children"),
     Output("chat-store", "data"),
     Output("user-input", "value", allow_duplicate=True),
     Output("message-count", "data"),
     Output("session-info", "children"),
     Output("thinking-display", "children"),
     Output("current-suggestions", "data")],
    [Input("send-button", "n_clicks"),
     Input("user-input", "n_submit")],
    [State("user-input", "value"),
     State("chat-store", "data"),
     State("chat-history", "children"),
     State("message-count", "data")],
    prevent_initial_call=True
)
def handle_chat(n_clicks, n_submit, user_input, chat_data, current_chat, message_count):
    if not user_input or not user_input.strip():
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    user_input = user_input.strip()
    
    # Add user message to chat with enhanced styling
    user_msg = html.Div([
        html.Div([
            html.Div([
                html.Span("You", className="fw-semibold"),
                html.Img(src="https://api.dicebear.com/7.x/avataaars/svg?seed=user&backgroundColor=667eea", 
                        style={"width": "28px", "height": "28px", "borderRadius": "50%", "marginLeft": "10px"}),
            ], className="d-flex align-items-center justify-content-end mb-2"),
            html.P(user_input, className="mb-0"),
        ], className="user-message"),
    ], className="mb-3 d-flex justify-content-end")
    
    # Get bot response with thinking process
    try:
        response, thinking_steps, suggestions = asyncio.run(get_bot_response_with_thinking(user_input))
    except Exception as e:
        response = f"Sorry, I encountered an error: {str(e)}\n\nPlease try again or rephrase your question."
        thinking_steps = [{"icon": "❌", "agent": "Error", "action": str(e)}]
        suggestions = []
    
    # Create thinking summary with enhanced styling (collapsed by default after response)
    thinking_summary = html.Div([
        dbc.Accordion([
            dbc.AccordionItem([
                html.Div([
                    html.Div([
                        html.Span(step.get("icon", "🔄"), className="me-2"),
                        dbc.Badge(step.get("agent", ""), pill=True, style={
                            "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                            "fontSize": "11px"
                        }, className="me-2"),
                        html.Span(step.get("action", ""), className="small text-muted"),
                    ], className="mb-2 p-2 rounded", style={"background": "rgba(102, 126, 234, 0.05)"})
                    for step in thinking_steps
                ])
            ], title=[
                html.I(className="fas fa-brain me-2"),
                f"Thinking Process ({len(thinking_steps)} steps)"
            ])
        ], start_collapsed=True, className="mb-3")
    ]) if thinking_steps else html.Div()
    
    # Create suggestions component
    suggestions_component = create_suggestion_buttons(suggestions) if suggestions else html.Div()
    
    # Add bot response to chat (with inline images if present)
    response_content = create_response_with_images(response)
    
    bot_msg = html.Div([
        html.Div([
            html.Div([
                html.Img(src="https://api.dicebear.com/7.x/bottts/svg?seed=assistant&backgroundColor=667eea", 
                        style={"width": "28px", "height": "28px", "borderRadius": "50%"}),
                html.Strong("Assistant", className="ms-2"),
            ], className="d-flex align-items-center mb-3"),
            thinking_summary,
            response_content,
            suggestions_component,
        ], className="bot-message"),
    ], className="mb-3")
    
    # Update chat history (replace loading message with actual response)
    new_chat = current_chat + [user_msg, bot_msg]
    
    # Update chat store
    new_chat_data = chat_data + [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": response}
    ]
    
    # Update message count
    new_count = message_count + 1
    
    # Update session info with enhanced styling
    session_info = [
        html.Div([
            html.Div([
                html.I(className="fas fa-comment-alt me-2", style={"color": "#667eea"}),
                html.Span("Messages", className="text-muted small"),
            ], className="d-flex align-items-center"),
            html.Strong(f"{new_count}", className="ms-auto", style={"color": "#667eea"}),
        ], className="d-flex align-items-center justify-content-between mb-2 p-2 rounded", 
           style={"background": "rgba(102, 126, 234, 0.1)"}),
        html.Div([
            html.Div([
                html.I(className="fas fa-clock me-2", style={"color": "#10b981"}),
                html.Span("Started", className="text-muted small"),
            ], className="d-flex align-items-center"),
            html.Strong(f"{datetime.now().strftime('%H:%M')}", className="ms-auto", style={"color": "#10b981"}),
        ], className="d-flex align-items-center justify-content-between p-2 rounded",
           style={"background": "rgba(16, 185, 129, 0.1)"}),
    ]
    
    # Clear thinking display after response
    thinking_display = html.Div()
    
    return new_chat, new_chat_data, "", new_count, session_info, thinking_display, suggestions


def generate_suggestions(user_input: str, response: str) -> list:
    """Generate contextual follow-up suggestions based on the conversation."""
    suggestions = []
    
    user_lower = user_input.lower()
    
    # Product-based suggestions
    if "iphone" in user_lower:
        suggestions.append("What are the top channels covering iPhone 17 Pro?")
        suggestions.append("What topics are discussed in iPhone 17 Pro videos?")
    elif "macbook" in user_lower:
        suggestions.append("What do creators say about MacBook Pro performance?")
        suggestions.append("Show me the most viewed MacBook Pro M5 videos")
    elif "chatgpt" in user_lower or "gpt" in user_lower:
        suggestions.append("What's the sentiment for ChatGPT GPT-5?")
        suggestions.append("What topics are discussed in ChatGPT videos?")
    
    # Query type suggestions
    if "top" in user_lower or "most" in user_lower:
        suggestions.append("Show me sentiment trends over time")
    elif "sentiment" in user_lower:
        suggestions.append("What are the most positive reviews?")
        suggestions.append("What are the common complaints?")
    elif "compare" in user_lower:
        suggestions.append("Show me a chart comparing these products")
    elif "transcript" in user_lower or "say" in user_lower:
        suggestions.append("What are the main topics discussed?")
    
    # Limit to 3 suggestions
    return suggestions[:3]


async def get_bot_response_with_thinking(user_input: str) -> tuple:
    """Get response from the multi-agent system with thinking process tracking."""
    global runner, session
    
    thinking_steps = []
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        return (
            "⚠️ **Error:** GOOGLE_API_KEY not found. Please set it in your .env file.",
            [{"icon": "❌", "agent": "System", "action": "API key not configured"}],
            []
        )
    
    # Step 1: Analyzing request
    thinking_steps.append({
        "icon": "🔍",
        "agent": "Coordinator",
        "action": "Analyzing your request..."
    })
    
    # Initialize runner and session if needed
    if runner is None:
        thinking_steps.append({
            "icon": "⚙️",
            "agent": "System",
            "action": "Initializing multi-agent system..."
        })
        runner = InMemoryRunner(coordinator_agent, app_name="youtube_chatbot")
        session = await runner.session_service.create_session(
            app_name="youtube_chatbot", 
            user_id="dashboard_user"
        )
    
    # Determine which agents might be used based on query
    user_lower = user_input.lower()
    
    if any(word in user_lower for word in ["top", "most", "views", "likes", "popular"]):
        thinking_steps.append({
            "icon": "📊",
            "agent": "YTMetaDataQueryBot",
            "action": "Searching video statistics..."
        })
    
    if any(word in user_lower for word in ["say", "mention", "discuss", "talk about", "transcript"]):
        thinking_steps.append({
            "icon": "🔍",
            "agent": "TranscriptRetriever",
            "action": "Searching video transcripts..."
        })
    
    if any(word in user_lower for word in ["think", "sentiment", "opinion", "feel", "review", "positive", "negative"]):
        thinking_steps.append({
            "icon": "💭",
            "agent": "SentimentAgent",
            "action": "Analyzing sentiment data..."
        })
    
    if any(word in user_lower for word in ["compare", "vs", "versus", "difference"]):
        thinking_steps.append({
            "icon": "⚖️",
            "agent": "ComparativeAgent",
            "action": "Comparing products..."
        })
    
    if any(word in user_lower for word in ["trend", "over time", "change", "timeline"]):
        thinking_steps.append({
            "icon": "📈",
            "agent": "TemporalAgent",
            "action": "Analyzing trends over time..."
        })
    
    if any(word in user_lower for word in ["chart", "plot", "graph", "visualize", "show"]):
        thinking_steps.append({
            "icon": "📉",
            "agent": "PlottingAgent",
            "action": "Generating visualization..."
        })
    
    # Create message
    message = types.Content(role='user', parts=[types.Part(text=user_input)])
    
    # Get response
    final_response = None
    try:
        async for event in runner.run_async(
            user_id="dashboard_user", 
            session_id=session.id, 
            new_message=message
        ):
            # Track agent activity from events
            if hasattr(event, 'author') and event.author:
                agent_name = event.author
                if agent_name != "CoordinatorAgent" and agent_name not in [s.get("agent") for s in thinking_steps]:
                    thinking_steps.append({
                        "icon": "🤖",
                        "agent": agent_name,
                        "action": "Processing..."
                    })
            
            if hasattr(event, 'is_final_response') and event.is_final_response():
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                break
            elif hasattr(event, 'content') and event.content and event.content.parts:
                if getattr(event, 'author', '') == coordinator_agent.name:
                    final_response = event.content.parts[0].text
    except Exception as e:
        return (
            f"⚠️ **Error:** {str(e)}",
            thinking_steps + [{"icon": "❌", "agent": "Error", "action": str(e)}],
            []
        )
    
    # Add completion step
    thinking_steps.append({
        "icon": "✅",
        "agent": "Coordinator",
        "action": "Response ready!"
    })
    
    if final_response:
        suggestions = generate_suggestions(user_input, final_response)
        return final_response, thinking_steps, suggestions
    else:
        return (
            "I couldn't generate a response. Please try rephrasing your question.",
            thinking_steps,
            ["What are the top iPhone 17 Pro videos?", "Tell me about ChatGPT GPT-5"]
        )


# Run the app
if __name__ == "__main__":
    print("\n" + "="*60)
    print("   🎬 YouTube Analytics Chatbot Dashboard")
    print("="*60)
    print("\n✅ Starting server...")
    print("🌐 Open http://127.0.0.1:8050 in your browser")
    print("\n📌 Features:")
    print("   • 7 specialized AI agents")
    print("   • Real-time thinking process display")
    print("   • Interactive examples and suggestions")
    print("   • Product-specific analysis")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    app.run(debug=True, host="0.0.0.0", port=8080)
