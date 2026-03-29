# Google Agent Development Kit (ADK)
## Complete Reference Documentation

**Version:** 1.19.0+  
**Last Updated:** November 2025  
**License:** Apache 2.0

---

## Executive Summary

The **Google Agent Development Kit (ADK)** is a production-ready, open-source framework for building, orchestrating, and deploying sophisticated AI agents and multi-agent systems. ADK is compatible with Python, Java, and Go, optimized for Gemini integration and Google Cloud deployment, yet remains model- and deployment-agnostic.

### Key Features

- **Modular Agent Architecture**: LLM Agents, Workflow Agents (Sequential/Parallel/Loop), Custom Agents
- **Rich Tool Integration**: Function tools, OpenAPI tools, MCP (Model Context Protocol), Google Cloud tools, third-party APIs
- **Session & State Management**: Multi-scoped state (session/user/temp), conversation memory, cross-session persistence
- **Workflow Orchestration**: Sequential pipelines, parallel execution, iterative loops
- **Safety & Guardrails**: Comprehensive callback system, content filtering, access control, rate limiting
- **Multi-Agent Coordination**: Hierarchical agent systems, delegation patterns, shared state communication
- **Production Deployment**: Vertex AI Agent Engine, Cloud Run, GKE, Docker, local deployment
- **Development Tools**: Web UI, CLI, API server, comprehensive debugging

---

## Table of Contents

1. Installation & Quick Start
2. Core Concepts & Architecture
3. Agent Types & Implementation
4. Tools & Integrations
5. Session, State & Memory Management
6. Runtime Execution Model
7. Multi-Agent Systems & Patterns
8. Safety, Callbacks & Guardrails
9. Deployment & Operations
10. API Reference & Configuration
11. Best Practices & Patterns
12. Resources & Community

---

## 1. Installation & Quick Start

### Prerequisites

- **Python 3.10+** (Java 17+ or Go for other runtimes)
- **Google Account** with API access
- **pip** or other package manager
- Optional: Google Cloud Project for Vertex AI

### Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\\Scripts\\activate  # Windows

# Install ADK
pip install google-adk

# Create new agent project
adk create my_agent

# Run in development
adk web                    # Launch browser UI at localhost:8000
adk run my_agent          # CLI mode
adk api_server            # Start REST API server
```

### Environment Configuration

**For Google AI Studio (development):**
```bash
# .env or environment variable
GOOGLE_API_KEY=your-api-key-here
```

**For Vertex AI (production):**
```bash
# .env
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Authenticate
gcloud auth application-default login
```

### Minimal Example

```python
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

# Define a simple tool
def greet(name: str) -> str:
    """Greets a person by name."""
    return f"Hello, {name}!"

# Create agent
agent = LlmAgent(
    name="greeter",
    model="gemini-2.0-flash",
    instruction="You are a friendly assistant.",
    tools=[greet]
)

# Run agent
runner = InMemoryRunner(agent, "my_app")
message = types.Content(role='user', parts=[types.Part(text="Hi!")])

async def main():
    session = await runner.session_service.create_session("my_app", "user_1")
    async for event in runner.run_async("user_1", session.id(), message):
        if event.is_final_response():
            print("Agent:", event.content.parts[0].text)

import asyncio
asyncio.run(main())
```

---

## 2. Core Concepts & Architecture

### Agents

An **Agent** is a self-contained execution unit that autonomously works toward specific goals:
- Perceives environment (user input, tool results)
- Reasons about next actions (LLM or deterministic logic)
- Takes actions (calls tools, sends responses)
- Updates state

**Agent Types:**
1. **LlmAgent**: Uses large language models for flexible, reasoning-based behavior
2. **SequentialAgent**: Executes sub-agents sequentially
3. **ParallelAgent**: Executes sub-agents concurrently
4. **LoopAgent**: Iteratively executes sub-agents until conditions met
5. **CustomAgent**: Extend BaseAgent for specialized logic

### Tools

**Tools** extend agent capabilities to interact with systems, APIs, and services:

- **Function Tools**: Python functions converted to tools
- **OpenAPI Tools**: Auto-generated from OpenAPI specs
- **MCP Tools**: Model Context Protocol servers
- **Built-in Tools**: Google Search, Code Execution
- **Cloud Tools**: BigQuery, Spanner, Vertex AI RAG, etc.
- **Agent Tools**: Convert other agents to tools for delegation

### Sessions

A **Session** represents a single conversation between a user and agent system:
- Contains chronological sequence of events and state
- Managed by SessionService (in-memory or persistent)
- Associated with specific app, user, and session ID
- Contains state dictionary for data storage

### State

**State** is data stored within a session, scoped by prefix:

| Scope | Prefix | Lifetime | Use Case |
|-------|--------|----------|----------|
| Session | (none) | Current session | Conversation context, current task |
| User | `user:` | Across all sessions | Preferences, history, settings |
| Temp | `temp:` | Single invocation | Intermediate values, computations |

### Events

**Events** are immutable records of occurrences during execution:
- User messages
- Agent responses
- Tool call requests
- Tool responses
- State deltas
- System events

Each event includes: author, content, timestamp, tool calls, state delta, actions.

### Memory

**Memory** is persistent, searchable knowledge across sessions:
- Semantically indexed by embedding
- Supports similarity search
- External data source integration
- Managed by MemoryService

### Runner

**Runner** orchestrates entire execution lifecycle:
- Loads/manages sessions
- Adds user messages
- Invokes agents
- Executes tools
- Updates state
- Persists events

---

## 3. Agent Types & Implementation

### LLM Agents

Leverage large language models for reasoning and generation:

```python
from google.adk.agents import LlmAgent
from google.genai import types

agent = LlmAgent(
    name="research_assistant",
    model="gemini-2.0-flash",
    description="Researches topics and provides summaries",
    instruction=\"\"\"
You are a research assistant. Your responsibilities:
1. Search for relevant information
2. Synthesize findings into clear summaries
3. Cite sources
4. Acknowledge uncertainty

Always provide balanced, factual information.
    \"\"\",

    # Configuration
    tools=[search_tool, summarize_tool],
    output_key="agent_response",

    # Include conversation history
    include_contents='all',  # 'all', 'last_n', 'none'

    # Model parameters
    generate_content_config=types.GenerateContentConfig(
        temperature=0.7,
        max_output_tokens=1024,
        top_p=0.95,
        safety_settings=[...]
    ),

    # Callbacks for safety/custom logic
    before_model_callback=my_before_callback,
    after_model_callback=my_after_callback,
    before_tool_callback=my_before_tool_callback,
    after_tool_callback=my_after_tool_callback,
)
```

**Key Features:**
- Dynamic tool selection based on user input
- Natural language reasoning
- Context-aware responses
- Flexible conversation management

### Workflow Agents

Orchestrate execution flow without LLM:

#### Sequential Agent
```python
from google.adk.agents import SequentialAgent

pipeline = SequentialAgent(
    name="data_pipeline",
    description="Extract, transform, load pipeline",
    sub_agents=[
        extract_agent,      # Fetches raw data
        transform_agent,    # Cleans and normalizes
        load_agent,         # Stores processed data
    ]
)
```

Executes agents one after another in specified order. State flows between agents.

#### Parallel Agent
```python
parallel_fetcher = ParallelAgent(
    name="concurrent_gatherer",
    sub_agents=[
        weather_agent,      # Fetches weather
        news_agent,         # Fetches news
        traffic_agent,      # Fetches traffic
    ]
)
```

Executes agents concurrently for speed. Useful for independent data gathering.

#### Loop Agent
```python
refiner = LoopAgent(
    name="iterative_refiner",
    sub_agents=[content_refiner, quality_checker],
    max_iterations=5,
    description="Refines content iteratively"
)
```

Repeats sub-agents until termination condition. Applications: refinement loops, retry logic.

### Custom Agents

Implement unique logic by extending BaseAgent:

```python
from google.adk.agents import BaseAgent
from google.adk.events import Event

class DatabaseQueryAgent(BaseAgent):
    """Custom agent for complex database operations."""

    def __init__(self, db_connection, **kwargs):
        super().__init__(**kwargs)
        self.db = db_connection

    async def _run_async_impl(self, context, new_message=None):
        # Extract query from message
        query_text = new_message.parts[0].text if new_message else ""

        # Custom validation
        if not self._validate_query(query_text):
            yield Event(
                author=self.name,
                content=types.Content(
                    role="model",
                    parts=[types.Part(text="Invalid query syntax")]
                )
            )
            return

        # Execute custom logic
        results = await self.db.query_async(query_text)

        # Generate response
        response_text = self._format_results(results)
        yield Event(
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text=response_text)]
            )
        )

    def _validate_query(self, query: str) -> bool:
        # Custom validation
        return len(query) > 0 and len(query) < 10000

    def _format_results(self, results) -> str:
        return f"Found {len(results)} results: {results[:100]}..."
```

---

## 4. Tools & Integrations

### Function Tools

Convert Python functions to tools:

```python
from google.adk.tools import FunctionTool

def calculate_loan_payment(
    principal: float,
    annual_rate: float,
    years: int
) -> dict:
    """Calculates monthly loan payment using standard formula.

    Args:
        principal: Loan amount in dollars
        annual_rate: Annual interest rate as percentage (e.g., 5.5)
        years: Loan duration in years

    Returns:
        Dictionary with monthly payment and total interest
    """
    monthly_rate = annual_rate / 100 / 12
    num_payments = years * 12

    if monthly_rate == 0:
        monthly_payment = principal / num_payments
    else:
        monthly_payment = principal * (
            monthly_rate * (1 + monthly_rate) ** num_payments
        ) / ((1 + monthly_rate) ** num_payments - 1)

    total_paid = monthly_payment * num_payments
    total_interest = total_paid - principal

    return {
        "monthly_payment": round(monthly_payment, 2),
        "total_interest": round(total_interest, 2),
        "total_paid": round(total_paid, 2)
    }

# Use directly
agent = LlmAgent(
    tools=[calculate_loan_payment]
)

# Or wrap explicitly
loan_tool = FunctionTool(func=calculate_loan_payment)
```

**Function Requirements:**
- Include descriptive docstring (used by LLM)
- Type hints on all parameters
- Return structured data (dict recommended)
- No default parameters currently

### Tool Context

Access agent state and context within tools:

```python
from google.adk.tools import ToolContext

def save_user_preference(
    preference: str,
    value: str,
    tool_context: ToolContext
) -> dict:
    """Saves user preference to state."""

    # Access invocation details
    user_id = tool_context.user_id
    session_id = tool_context.session_id

    # Read from state
    prefs_key = "user:preferences"
    preferences = tool_context.state.get(prefs_key, {})

    # Update
    preferences[preference] = value
    tool_context.state[prefs_key] = preferences

    return {
        "status": "success",
        "saved": {preference: value}
    }
```

**Available in ToolContext:**
- `tool_context.state` - Read/write session state
- `tool_context.session_id` - Current session ID
- `tool_context.user_id` - Current user ID
- `tool_context.invocation_id` - Current invocation ID
- `tool_context.function_call_id` - Tool call ID

### OpenAPI Tools

Auto-generate tools from OpenAPI specs:

```python
from google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset import OpenAPIToolset

# Load from JSON string
openapi_json = '''
{
  "openapi": "3.0.0",
  "info": {"title": "My API", "version": "1.0.0"},
  ...
}
'''

toolset = OpenAPIToolset(spec_str=openapi_json, spec_str_type="json")
api_tools = toolset.get_tools()

agent = LlmAgent(name="api_agent", tools=api_tools)
```

### MCP (Model Context Protocol) Tools

Integrate standardized MCP servers:

```python
from google.adk.tools import MCPToolset

# Connect to MCP server
mcp_toolset = MCPToolset(
    server_script_path="path/to/mcp_server.py"
)

mcp_tools = await mcp_toolset.get_tools_async()

agent = LlmAgent(tools=mcp_tools)
```

### Agents as Tools

Convert specialized agents to tools for delegation:

```python
from google.adk.tools import agent_tool

# Specialized agent
translator = LlmAgent(
    name="translator",
    instruction="Translate text to target language"
)

# Convert to tool
translator_tool = agent_tool(translator)

# Use in parent agent
multi_lingual = LlmAgent(
    name="multi_lingual_agent",
    tools=[translator_tool]
)
```

---

## 5. Session, State & Memory Management

### Session Lifecycle

```python
from google.adk.sessions import InMemorySessionService

service = InMemorySessionService()

# Create session
session = await service.create_session(
    app_name="customer_support",
    user_id="user_123",
    session_id="session_456",
    state={
        "user:language": "en",
        "user:support_tier": "premium"
    }
)

# Retrieve session
session = await service.get_session(
    app_name="customer_support",
    user_id="user_123",
    session_id="session_456"
)

# List sessions for user
sessions = await service.list_sessions(
    app_name="customer_support",
    user_id="user_123"
)

# Delete session
await service.delete_session(
    app_name="customer_support",
    user_id="user_123",
    session_id="session_456"
)
```

### State Scopes

```python
# Session state (conversation-specific)
session.state["current_topic"] = "product_support"
session.state["conversation_turn"] = 5

# User state (persists across sessions)
session.state["user:account_status"] = "active"
session.state["user:total_tickets"] = 42
session.state["user:language"] = "es"

# Temp state (single invocation, auto-cleared)
session.state["temp:validation_needed"] = True
session.state["temp:intermediate_result"] = compute_something()
```

### State Access Patterns

```python
# Read with default
language = session.state.get("user:language", "en")

# Direct access (raises KeyError if absent)
try:
    tier = session.state["user:support_tier"]
except KeyError:
    tier = "standard"

# Check existence
if "user:preferences" in session.state:
    apply_preferences(session.state["user:preferences"])

# Update nested
session.state["user:preferences"]["theme"] = "dark"

# Batch update (in callbacks)
session.state.update({
    "current_step": 2,
    "user:visits": session.state.get("user:visits", 0) + 1
})
```

### State Delta Updates

Update state outside of normal agent execution:

```python
from google.adk.events import Event, EventActions
import time

# Define state changes
state_changes = {
    "task_completed": True,
    "user:login_count": session.state.get("user:login_count", 0) + 1
}

# Create state delta event
actions = EventActions(state_delta=state_changes)
system_event = Event(
    author="system",
    content=None,
    actions=actions,
    timestamp=time.time()
)

# Append (applies state changes)
await session_service.append_event(session, system_event)
```

### Persistent Session Storage

For production, use persistent backend:

```python
# PostgreSQL
from google.adk.sessions import PostgresSessionService

session_service = PostgresSessionService(
    connection_string="postgresql://user:pass@host/database"
)

# Firestore
from google.adk.sessions import FirestoreSessionService

session_service = FirestoreSessionService(
    project_id="my-gcp-project"
)
```

### Memory Service

For cross-session knowledge:

```python
from google.adk.memory import MemoryService

memory = MemoryService()

# Ingest information
await memory.ingest(
    data="Customer prefers email contact",
    metadata={"user_id": "user_123", "timestamp": "2025-11-24"}
)

# Search memory
results = await memory.search(
    query="user_123 communication preferences",
    top_k=5
)

# Results: [{"content": "...", "similarity": 0.95, "metadata": {...}}, ...]
```

---

## 6. Runtime Execution Model

### Runner Types

```python
# In-memory (session service created automatically)
from google.adk.runners import InMemoryRunner

runner = InMemoryRunner(
    agent=my_agent,
    app_name="my_app"
)

# With explicit session service
from google.adk.runners import Runner
from google.adk.sessions import PostgresSessionService

session_service = PostgresSessionService(...)
runner = Runner(
    agent=my_agent,
    app_name="my_app",
    session_service=session_service
)
```

### Agent Execution

```python
from google.genai import types

# Prepare message
user_message = types.Content(
    role='user',
    parts=[types.Part(text="What's the weather in Paris?")]
)

# Run agent (async)
events = runner.run_async(
    user_id="user_123",
    session_id="session_456",
    new_message=user_message
)

# Process events
async for event in events:
    # User-visible response
    if event.is_final_response():
        print("Agent:", event.content.parts[0].text)

    # Tool calls
    if event.get_function_calls():
        for call in event.get_function_calls():
            print(f"Calling tool: {call.name}")

    # State changes
    if event.actions and event.actions.state_delta:
        print("State updated:", event.actions.state_delta)

    # Events stream is infinite; break on final response
    if event.is_final_response():
        break
```

### Event Loop Phases

1. **Input**: User sends message
2. **Start**: Runner loads session, adds message event
3. **Agent Invoke**: Main agent begins execution
4. **Reasoning**: Agent (LLM or logic) determines next action
5. **Tool Planning**: Decide which tools to call
6. **Tool Execution**: Runner executes tool calls
7. **Tool Results**: Feed results back to agent
8. **Response Generation**: Agent formulates final response
9. **State Update**: Session state modified
10. **Finalization**: Session saved, events persisted

### Streaming Events

Handle events as they arrive:

```python
async for event in runner.run_async(...):
    event_type = event.__class__.__name__

    print(f"Event: {event_type}")
    print(f"  Author: {event.author}")
    print(f"  Timestamp: {event.timestamp}")

    # Incremental processing
    if hasattr(event, 'content') and event.content:
        if event.content.parts:
            for part in event.content.parts:
                if hasattr(part, 'text'):
                    print(f"  Text: {part.text[:100]}...")
```

---

## 7. Multi-Agent Systems & Patterns

### Agent Hierarchy

```
Root Coordinator (LLM Agent)
├── Specialist: Email Handler
├── Specialist: Billing Agent
├── Specialist: Technical Support
└── Workflow: Escalation Pipeline
    ├── Logger
    ├── Ticket Creator
    └── Manager Notifier
```

### Communication: Shared State

```python
# Agent 1: Researcher (stores output in state)
researcher = LlmAgent(
    name="researcher",
    output_key="research_findings",
    instruction="Research and summarize findings"
)

# Agent 2: Analyst (reads from state via template)
analyst = LlmAgent(
    name="analyst",
    instruction="""
Analyze the following research findings:
{research_findings}

Provide insights and recommendations.
    """
)

# Sequential execution (state flows forward)
pipeline = SequentialAgent(
    name="research_pipeline",
    sub_agents=[researcher, analyst]
)
```

### Communication: Agent Delegation

```python
# Specialist agents
support_agent = LlmAgent(
    name="support_specialist",
    description="Handles customer support"
)

billing_agent = LlmAgent(
    name="billing_specialist",
    description="Handles billing inquiries"
)

# Root agent delegates to specialists
root = LlmAgent(
    name="customer_service",
    instruction="""
You are a customer service router.

If the customer has a support issue, delegate to support_specialist.
If it's about billing, delegate to billing_specialist.
For general inquiries, handle directly.

Always be polite and professional.
    """,
    tools=[
        agent_tool(support_agent),
        agent_tool(billing_agent)
    ]
)
```

### Common Patterns

#### Supervisor Pattern
Single coordinator directs multiple specialists:

```python
supervisor = LlmAgent(
    name="supervisor",
    tools=[
        agent_tool(data_engineer),
        agent_tool(analyst),
        agent_tool(reporter)
    ]
)
```

#### Pipeline Pattern
Sequential stages with state passing:

```python
pipeline = SequentialAgent(
    sub_agents=[
        fetch_agent,       # Gets raw data (output_key="raw_data")
        clean_agent,       # Cleans data (uses raw_data)
        analyze_agent,     # Analyzes (uses cleaned_data)
        report_agent       # Generates report
    ]
)
```

#### Parallel Aggregation Pattern
Fetch data concurrently, then synthesize:

```python
# Parallel gathering
gatherer = ParallelAgent(
    name="data_gatherer",
    sub_agents=[
        weather_fetcher,   # output_key="weather"
        news_fetcher,      # output_key="news"
        traffic_fetcher    # output_key="traffic"
    ]
)

# Synthesis
synthesizer = LlmAgent(
    name="synthesizer",
    instruction="""
Based on:
- Weather: {weather}
- News: {news}
- Traffic: {traffic}

Provide daily briefing.
    """
)

# Complete
briefing_system = SequentialAgent(
    sub_agents=[gatherer, synthesizer]
)
```

#### Retry/Recovery Pattern

```python
reliability_loop = LoopAgent(
    name="reliable_processor",
    sub_agents=[
        processor_agent,
        validator_agent
    ],
    max_iterations=3
)
```

---

## 8. Safety, Callbacks & Guardrails

### Callback System

Intercept and modify agent behavior at key points:

#### Before Model Callback

Inspect/modify requests before LLM call:

```python
def content_safety_filter(
    callback_context,
    llm_request
) -> Optional[LlmResponse]:
    """Filter harmful content before LLM processes."""

    # Get user message
    user_msg = llm_request.contents[-1].parts[0].text.lower()

    # Block dangerous content
    forbidden = ["illegal", "harmful", "violence"]
    if any(word in user_msg for word in forbidden):
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(
                    text="I cannot help with that request."
                )]
            )
        )

    return None  # Proceed normally

agent = LlmAgent(
    name="safe_agent",
    before_model_callback=content_safety_filter
)
```

#### After Model Callback

Filter or modify LLM response:

```python
def redact_sensitive_data(callback_context, llm_response):
    """Remove sensitive information from response."""

    response_text = llm_response.content.parts[0].text

    # Redact patterns
    import re
    response_text = re.sub(r'\d{3}-\d{2}-\d{4}', '[SSN]', response_text)
    response_text = re.sub(r'\d{16}', '[CC]', response_text)

    llm_response.content.parts[0].text = response_text
    return llm_response

agent = LlmAgent(after_model_callback=redact_sensitive_data)
```

#### Before Tool Callback

Validate/authorize tool calls:

```python
def enforce_access_control(callback_context, tool_name, tool_args):
    """Check permissions before tool execution."""

    user_role = callback_context.state.get("user:role", "user")

    # Admin-only tools
    admin_tools = ["delete_data", "modify_config", "export_report"]
    if tool_name in admin_tools and user_role != "admin":
        return {"error": f"Unauthorized: {tool_name} requires admin role"}

    # Rate limiting
    call_count_key = f"tool_calls:{tool_name}"
    count = callback_context.state.get(call_count_key, 0)
    if count > 100:
        return {"error": "Rate limit exceeded"}

    # Log call
    callback_context.state[call_count_key] = count + 1

    return None  # Proceed

agent = LlmAgent(before_tool_callback=enforce_access_control)
```

#### After Tool Callback

Process/cache tool results:

```python
def cache_results(callback_context, tool_name, tool_args, tool_result):
    """Cache tool results for performance."""

    # Generate cache key
    import hashlib
    args_hash = hashlib.md5(str(tool_args).encode()).hexdigest()
    cache_key = f"cache:{tool_name}:{args_hash}"

    # Store result
    if isinstance(tool_result, dict):
        callback_context.state[cache_key] = tool_result

    # Add metadata
    tool_result["_cached"] = False
    tool_result["_cache_key"] = cache_key

    return tool_result

agent = LlmAgent(after_tool_callback=cache_results)
```

### Safety Patterns

#### Input Validation

```python
def validate_inputs(context, request):
    for msg in request.contents:
        for part in msg.parts:
            if hasattr(part, 'text') and len(part.text) > 100000:
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text="Input too long")]
                    )
                )
    return None
```

#### Rate Limiting

```python
def rate_limiter(context, tool_name, tool_args):
    user_key = f"user:{context.user_id}:calls_today"
    count = context.state.get(user_key, 0)

    if count >= 1000:
        return {"error": "Daily limit reached"}

    context.state[user_key] = count + 1
    return None
```

#### Cost Control

```python
def cost_monitor(context, tool_name, tool_args):
    # Expensive operations
    if tool_name in ["process_large_file", "run_simulation"]:
        if context.state.get("user:tier") != "premium":
            return {"error": "Feature requires premium"}

    return None
```

### Plugins

Reusable guardrails:

```python
from google.adk.plugins import BasePlugin

class SecurityPlugin(BasePlugin):
    def before_model(self, context, request):
        # Security checks
        pass

    def before_tool(self, context, tool_name, tool_args):
        # Access control
        pass

# Apply to multiple agents
plugin = SecurityPlugin()
agent1 = LlmAgent(..., plugins=[plugin])
agent2 = LlmAgent(..., plugins=[plugin])
```

---

## 9. Deployment & Operations

### Deployment Options

#### Vertex AI Agent Engine

Fully managed service:

```bash
# Deploy
adk deploy --platform=agent-engine \
  --project=my-project \
  --location=us-central1
```

**Features:**
- Auto-scaling
- Managed infrastructure
- Built-in monitoring
- Session management

#### Google Cloud Run

Container-based deployment:

```python
# main.py - FastAPI server
from fastapi import FastAPI
from google.adk.agents import LlmAgent

app = FastAPI()
agent = LlmAgent(...)

@app.post("/run")
async def run_agent(payload: dict):
    # Execute agent
    ...

# Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

```bash
# Deploy
gcloud run deploy my-agent \
  --source . \
  --region us-central1
```

#### GKE (Kubernetes)

For enterprise deployments:

```bash
# Build and push container
docker build -t gcr.io/my-project/my-agent .
docker push gcr.io/my-project/my-agent

# Deploy with kubectl
kubectl apply -f deployment.yaml
```

#### Local / Docker Development

```bash
# Build
docker build -t my-agent .

# Run
docker run -p 8080:8080 my-agent
```

### Development Tools

#### Web UI

```bash
adk web

# Access: http://localhost:8000
```

Features:
- Chat interface
- Agent selection
- Event inspection
- Trace logs
- Performance metrics

#### CLI

```bash
adk run my_agent
adk run my_agent < input.txt
echo "Hello" | adk run my_agent
```

#### API Server

```bash
adk api_server

# POST /apps/my_app/run
curl -X POST http://localhost:8000/apps/my_app/run \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "session_id": "session_456",
    "message": "Hello"
  }'
```

### Monitoring & Observability

#### Logging

```python
import logging

logger = logging.getLogger(__name__)

def after_model(context, response):
    logger.info(f"Agent {context.agent_name} responded to {context.user_id}")
    logger.debug(f"Response: {response.content.parts[0].text[:100]}")
    return response
```

#### Tracing

```python
from arize.otel import register
from openinference.instrumentation.google_adk import GoogleADKInstrumentor

tracer_provider = register(
    space_id="your-space-id",
    api_key="your-api-key"
)
GoogleADKInstrumentor().instrument(tracer_provider=tracer_provider)
```

#### Metrics

```python
import time

def track_metrics(context, request):
    context.state["start_time"] = time.time()
    return None

def after_model_metrics(context, response):
    elapsed = time.time() - context.state.get("start_time", 0)
    # Send to monitoring system
    return response
```

---

## 10. API Reference & Configuration

### Python API Modules

```python
# Core agents
from google.adk.agents import (
    Agent,                  # LlmAgent alias
    LlmAgent,              # LLM-based agent
    SequentialAgent,       # Sequential execution
    ParallelAgent,         # Parallel execution
    LoopAgent,             # Iterative execution
    BaseAgent              # Extend for custom
)

# Tools
from google.adk.tools import (
    FunctionTool,          # Wrap functions
    agent_tool,            # Convert agent to tool
    google_search,         # Built-in search
    code_execution         # Code executor
)

# Runtime
from google.adk.runners import (
    Runner,                # Manual session service
    InMemoryRunner         # Auto session service
)

# Sessions
from google.adk.sessions import (
    InMemorySessionService,    # Local storage
    PostgresSessionService,    # Database
    FirestoreSessionService    # Cloud Firestore
)

# Events
from google.adk.events import (
    Event,
    EventActions
)

# Models
from google.adk.models import (
    LlmRequest,
    LlmResponse
)

# Callbacks
from google.adk.agents.callback_context import CallbackContext

# Gemini types
from google.genai import types
```

### CLI Commands

```bash
# Project management
adk create [--type=config] <name>    # Create agent
adk delete <name>                     # Delete agent

# Development
adk run <agent_name>                  # Terminal mode
adk web [--no-reload]                # Web UI
adk api_server                        # API server

# Deployment
adk deploy --platform=agent-engine   # Deploy to Vertex AI

# Utilities
adk --version                         # Show version
adk --help                            # Show help
```

### Configuration

#### .env File

```bash
# Google AI Studio (development)
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your-api-key

# Vertex AI (production)
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project
GOOGLE_CLOUD_LOCATION=us-central1

# Custom settings
APP_NAME=my_app
DEBUG=true
```

#### Agent Config (YAML)

```yaml
# config.yaml
agent_class: LlmAgent
name: my_agent
model: gemini-2.0-flash
description: "My awesome agent"

instruction: |
  You are a helpful assistant.
  Answer questions accurately.

tools:
  - type: google_search
  - type: function
    name: my_tool
    module: tools
    function: my_tool_func

generate_content_config:
  temperature: 0.7
  max_output_tokens: 1024
  top_p: 0.95

output_key: agent_output
```

---

## 11. Best Practices & Patterns

### Agent Design

**1. Clear Instructions**
```python
instruction="""
You are a customer service representative for TechCorp.

Your responsibilities:
1. Help customers troubleshoot technical issues
2. Process refund requests (up to \$100 without approval)
3. Escalate to supervisor for complex issues
4. Always maintain professional, empathetic tone

Never promise discounts not in your authority.
"""
```

**2. Focused Scope**
- Each agent should have clear, bounded responsibility
- Avoid multi-purpose agents; use delegation instead
- Single responsibility principle

**3. Appropriate Tools**
- Include only necessary tools
- Too many confuses LLM decision-making
- Organize related tools logically

### State Management Best Practices

**1. Initialize Early**
```python
session = await service.create_session(
    state={
        "user:language": "en",
        "user:timezone": "UTC",
        "conversation_history": []
    }
)
```

**2. Use Appropriate Scopes**
- Session: Current conversation context
- User: Persistent preferences and history
- Temp: Single-invocation computations

**3. State as Documentation**
- Descriptive key names
- Type consistency within keys
- Document expected state structure

### Tool Development

**1. Comprehensive Docstrings**
```python
def query_product_db(
    category: str,
    max_results: int = 10,
    sort_by: str = "popularity"
) -> dict:
    """Search product database for items.

    Queries the product database and returns matching items
    sorted by specified criteria.

    Args:
        category: Product category (e.g., 'electronics', 'clothing')
        max_results: Maximum results to return (1-100, default 10)
        sort_by: Sort criteria - 'popularity', 'price', 'rating'

    Returns:
        Dictionary with:
            - status: 'success' or 'error'
            - products: List of product objects
            - count: Number of results returned
            - total: Total matching items available

    Raises:
        ValueError: If category is invalid or max_results out of range
    """
```

**2. Structured Returns**
```python
# Good
return {
    "status": "success",
    "data": [...],
    "count": 5,
    "timestamp": datetime.now().isoformat()
}

# Bad
return [...]  # Ambiguous for empty results
return "Success"  # Not structured
```

**3. Error Handling**
```python
def my_tool(arg: str) -> dict:
    try:
        result = perform_operation(arg)
        return {
            "status": "success",
            "result": result
        }
    except ValueError as e:
        return {
            "status": "error",
            "error_code": "INVALID_INPUT",
            "error_message": str(e)
        }
    except Exception as e:
        return {
            "status": "error",
            "error_code": "INTERNAL_ERROR",
            "error_message": "An unexpected error occurred"
        }
```

### Multi-Agent Systems

**1. Hierarchical Organization**
- Coordinator at top level
- Specialists below
- Clear delegation logic

**2. State Communication**
```python
agent1 = LlmAgent(output_key="analysis_results", ...)
agent2 = LlmAgent(instruction="Use: {analysis_results}", ...)
```

**3. Monitoring Coordination**
- Log delegation decisions
- Track success rates
- Monitor cost per agent

### Performance Optimization

**1. Use Parallel Agents**
```python
# For independent operations
parallel = ParallelAgent(sub_agents=[task1, task2, task3])
```

**2. Cache Results**
```python
def expensive_tool(query: str, context: ToolContext):
    cache_key = f"cache:{query}"
    if cache_key in context.state:
        return context.state[cache_key]

    result = expensive_operation(query)
    context.state[cache_key] = result
    return result
```

**3. Choose Appropriate Models**
- `gemini-2.0-flash`: Default, balanced
- `gemini-2.0-flash-lite`: Fast, simple tasks
- `gemini-pro`: Advanced reasoning, complex tasks

### Security Best Practices

**1. Input Validation**
```python
def before_tool_validate(context, tool_name, tool_args):
    # Validate all inputs
    if len(tool_args.get("query", "")) > 10000:
        return {"error": "Query too long"}
    return None
```

**2. Access Control**
```python
def check_authorization(context, tool_name, tool_args):
    required_role = {"delete_user": "admin", "export_data": "analyst"}

    if tool_name in required_role:
        user_role = context.state.get("user:role")
        if user_role != required_role[tool_name]:
            return {"error": "Insufficient permissions"}
    return None
```

**3. Output Filtering**
```python
def redact_output(context, response):
    import re
    text = response.content.parts[0].text

    # Remove PII
    text = re.sub(r'\d{3}-\d{2}-\d{4}', '[SSN]', text)

    response.content.parts[0].text = text
    return response
```

**4. Rate Limiting**
```python
def rate_limit(context, tool_name, tool_args):
    key = f"rate:{context.user_id}:{tool_name}"
    count = context.state.get(key, 0)

    if count > 10:
        return {"error": "Rate limit exceeded"}

    context.state[key] = count + 1
    return None
```

### Testing Strategies

**1. Unit Test Tools**
```python
def test_query_tool():
    result = query_product_db("electronics", max_results=5)

    assert result["status"] == "success"
    assert len(result["products"]) <= 5
    assert result["count"] <= 5
```

**2. Integration Test Agents**
```python
async def test_agent_flow():
    runner = InMemoryRunner(agent)

    message = types.Content(role='user', parts=[...])
    events = runner.run_async("test_user", "test_session", message)

    response_text = None
    async for event in events:
        if event.is_final_response():
            response_text = event.content.parts[0].text
            break

    assert response_text is not None
    assert len(response_text) > 0
```

---

## 12. Resources & Community

### Official Resources

- **Documentation**: https://google.github.io/adk-docs/
- **GitHub**: https://github.com/google/adk-python
- **Examples**: https://github.com/google/adk-docs/tree/main/examples
- **API Reference**: https://google.github.io/adk-docs/api-reference/

### Learning Resources

- **Codelabs**: Building AI Agents with ADK (Foundation)
- **Tutorials**: Multi-tool agent, team workflows, deployment
- **Blog**: Agent patterns and best practices
- **YouTube**: ADK demonstrations and walkthroughs

### Community & Support

- **GitHub Issues**: Report bugs, request features
- **Discussions**: Ask questions, share patterns
- **Stack Overflow**: Tag with `google-adk`
- **Reddit**: r/agentdevelopmentkit

### Related Technologies

- **Gemini API**: https://ai.google.dev/gemini-api
- **Vertex AI**: https://cloud.google.com/vertex-ai
- **Model Context Protocol (MCP)**: https://modelcontextprotocol.io
- **LangChain**: Integration patterns
- **LlamaIndex**: Data indexing patterns

---

## Quick Reference

### Imports

```python
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent, LoopAgent
from google.adk.tools import FunctionTool, agent_tool, ToolContext
from google.adk.runners import Runner, InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.adk.events import Event, EventActions
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types
```

### Minimal Agent

```python
agent = LlmAgent(
    name="my_agent",
    model="gemini-2.0-flash",
    instruction="You are helpful",
    tools=[my_tool]
)
```

### Minimal Execution

```python
runner = InMemoryRunner(agent, "my_app")
session = await runner.session_service.create_session("my_app", "user_1")

message = types.Content(role='user', parts=[types.Part(text="Hello")])
async for event in runner.run_async("user_1", session.id(), message):
    if event.is_final_response():
        print(event.content.parts[0].text)
        break
```

---

## Version & License

- **Version**: 1.19.0+ (requires Python 3.10+)
- **License**: Apache 2.0
- **Last Updated**: November 2025

---

*Comprehensive Google ADK documentation compiled from official sources for AI/LLM consumption*
