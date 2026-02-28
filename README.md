<!-- pyml disable-next-line no-inline-html -->
<div align="center">

# CRUSE Agentic UI

**Context Reactive User Experience — The UI Itself Is an Agent**

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776ab?logo=python&logoColor=white)](https://python.org)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-000000?logo=next.js&logoColor=white)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.133-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MUI 5](https://img.shields.io/badge/MUI-5-007FFF?logo=mui&logoColor=white)](https://mui.com)
[![Neuro SAN](https://img.shields.io/badge/Neuro_SAN-0.6.35-ff6f00)](https://github.com/cognizant-ai-lab/neuro-san)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

An agentic frontend for [Neuro SAN](https://github.com/cognizant-ai-lab/neuro-san) multi-agent networks — with dynamic AI-generated widgets, real-time agent tracing, and interactive network visualization.

</div>

---

### Demo

https://github.com/user-attachments/assets/8cf88c66-c8c4-42dd-972b-df086c228ab9

---

<!-- pyml disable-next-line no-inline-html -->
<div align="center">

**Dynamic Widgets** — AI generates forms on the fly | **Live Tracing** — Watch agents communicate in real time | **Network Graph** — Interactive SVG topology

</div>

---

## Credits and Acknowledgments

The original **CRUSE (Context Reactive User Experience)** concept and implementation were
created by the **Cognizant AI Lab** team as part of the
[Neuro SAN Studio](https://github.com/cognizant-ai-lab/neuro-san-studio) project. The
original Flask-based interface, core assistant logic, CRUSE agent network definition, and
the coded tools that power widget generation are all authored and maintained by Cognizant
Technology Solutions Corp under the Apache License 2.0.

**CRUSE Agentic UI** is a full-stack rebuild of the frontend and backend that preserves the
original agent logic while modernizing the delivery layer with Next.js, FastAPI, and
real-time WebSocket streaming. The original Flask + SocketIO implementation remains intact
for backward compatibility.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [What We Built on Top](#what-we-built-on-top)
3. [Backend (FastAPI)](#backend-fastapi)
4. [Frontend (Next.js)](#frontend-nextjs)
5. [HOCON Configuration](#hocon-configuration)
6. [Agent Network Visualization](#agent-network-visualization)
7. [WebSocket Protocol](#websocket-protocol)
8. [Widget System](#widget-system)
9. [Running the Application](#running-the-application)
10. [Project Structure](#project-structure)
11. [Future Improvements](#future-improvements)

---

## Architecture Overview

```
                        CRUSE Next-Gen Architecture
 +------------------------------------------------------------------+
 |                                                                    |
 |   Browser (Next.js 14)          FastAPI Backend                    |
 |  +---------------------+      +----------------------------+      |
 |  |                     |      |                            |      |
 |  |  Zustand Store      | REST |  Session Manager           |      |
 |  |  +-----------+      |<---->|  +------------------+      |      |
 |  |  | sessions  |      |      |  | CruseSession     |      |      |
 |  |  | messages  |      |      |  | (eager init)     |      |      |
 |  |  | widgets   |      |  WS  |  +------------------+      |      |
 |  |  | theme     |      |<---->|                            |      |
 |  |  | traces    |      |      |  Streaming Bridge           |      |
 |  |  +-----------+      |      |  +------------------+      |      |
 |  |                     |      |  | parse responses  |      |      |
 |  |  MUI + Framer       |      |  | say: / gui:      |      |      |
 |  |  Motion UI          |      |  +------------------+      |      |
 |  |                     |      |                            |      |
 |  |  Network Graph      |      |  Connectivity Reporter     |      |
 |  |  (live SVG)         |      |  (CRUSE + target merge)    |      |
 |  +---------------------+      +----------------------------+      |
 |                                          |                         |
 |                                          v                         |
 |                               Neuro SAN Agent Runtime              |
 |                              +------------------------+            |
 |                              |  cruse (front-man)     |            |
 |                              |    +-> domain_expert   |            |
 |                              |    |     +-> target    |            |
 |                              |    |        network    |            |
 |                              |    +-> widget_generator|            |
 |                              |         +-> template   |            |
 |                              |            _provider   |            |
 |                              +------------------------+            |
 +------------------------------------------------------------------+
```

### The CRUSE Agent Chain

When a user sends a message, it flows through a three-tier agent orchestration:

1. **`cruse`** (Front-man LLM Agent) -- Receives user input and UI state, orchestrates
   the response by calling its two tools in sequence.

2. **`domain_expert`** (Coded Tool / CallAgent) -- Delegates the actual question to
   whichever agent network the user selected (e.g., `basic/hello_world`,
   `industry/airline_policy`). Uses the AAOSA protocol in a two-phase pattern:
   *Determine* (is this relevant?) then *Fulfill* (answer it).

3. **`widget_generator`** (LLM Agent) -- Analyzes the conversation context and decides
   whether to generate a JSON Schema form widget. Calls `template_provider` to get
   schema templates and field-type examples, then produces a widget definition or
   `{"display": false}` if no form is needed.

---

## What We Built on Top

The original CRUSE implementation is a Flask app with SocketIO that runs a blocking
agent loop in a background thread. It works, but has limitations around concurrency,
modern UI patterns, and developer experience.

CRUSE Next-Gen adds the following layers **without modifying** the original code:

### Backend Rebuild (FastAPI + WebSocket)

| Component | File | Purpose |
|-----------|------|---------|
| FastAPI server | `backend/main.py` | REST + WebSocket endpoints, CORS, lifecycle |
| Session manager | `backend/session_manager.py` | Multi-session with eager background init |
| Streaming bridge | `backend/streaming_bridge.py` | Bridges sync agent calls to async WebSocket events |
| Response parser | `backend/response_parser.py` | Enhanced `say:`/`gui:` parser with JSON detection |
| Theme service | `backend/theme_service.py` | Tag-based theme selection from HOCON metadata |
| Session store | `backend/session_store.py` | Session timeout cleanup (30-minute TTL) |
| Debug processor | `backend/debug_message_processor.py` | Real-time agent trace capture |
| Log capture | `backend/log_capture.py` | Ring buffer for server log streaming |
| Pydantic models | `backend/models.py` | Typed WebSocket protocol definitions |

### Frontend Rebuild (Next.js 14 + MUI 5 + Zustand)

| Component | File(s) | Purpose |
|-----------|---------|---------|
| Layout shell | `CruseLayout.tsx` | Full-height flex layout with widget/chat split |
| Header bar | `Header.tsx` | Network selector, new chat, theme toggle, drawers |
| Chat panel | `chat/ChatPanel.tsx` | Scrollable message list with markdown rendering |
| Input bar | `InputBar.tsx` | Text input + form data attachment |
| Widget card | `widget/WidgetCard.tsx` | JSON Schema form renderer with success animation |
| Schema form | `widget/SchemaForm.tsx` | RJSF wrapper with 5 custom field widgets |
| Dynamic icon | `widget/DynamicIcon.tsx` | Runtime MUI icon resolution |
| Background engine | `theme/BackgroundEngine.tsx` | CSS-doodle + gradient background renderer |
| Agent activity | `activity/AgentActivityBar.tsx` | Pulsing pill indicators for active agents |
| Debug drawer | `debug/DebugDrawer.tsx` | Agent trace + server log viewer |
| Network drawer | `network/NetworkDrawer.tsx` | Full-screen agent network visualization |
| Network graph | `network/NetworkGraph.tsx` | Live SVG graph with traveling dot animations |
| Spotlight tour | `tour/SpotlightTour.tsx` | First-use walkthrough overlay |
| WebSocket hook | `hooks/useWebSocket.ts` | Connection management + event routing |
| Zustand store | `store/cruseStore.ts` | Centralized state (sessions, UI, debug, network) |

### Agent Network Visualization

| Component | File | Purpose |
|-----------|------|---------|
| Merged connectivity | `backend/session_manager.py` | Merges CRUSE orchestrator + target network graphs |
| REST endpoint | `backend/main.py` | `GET /api/connectivity/{network}` |
| Graph layout | `network/NetworkGraph.tsx` | BFS tree layout + SVG rendering |
| Live tracing | `network/NetworkGraph.tsx` | Dot-delimited origin parsing, active node/edge tracking |

---

## Backend (FastAPI)

### Session Lifecycle

```
POST /api/session {agent_network: "basic/hello_world"}
  |
  v
SessionManager.create_session()
  |-- Creates CruseSession(session_id, agent_network)
  |-- Starts eager init in background thread (13s setup)
  |-- Returns session_id immediately
  |
  v
WebSocket connects: ws://localhost:5001/ws/chat/{session_id}
  |
  v
User sends: {"text": "Hello", "form_data": null}
  |
  v
process_chat_message()
  |-- Runs CruseSession.chat() in thread pool
  |-- Polls every 2s: drains debug events, sends keepalive
  |-- On completion: parses response blocks
  |-- Emits: chat_complete, widget_schema, agent_trace, done
```

### Eager Session Initialization

The most expensive operation is creating the Neuro SAN agent session (~13 seconds).
CRUSE Next-Gen uses **eager background initialization**: the session starts building in
a daemon thread the moment `POST /api/session` is called. If the user sends their first
message before init finishes, it blocks until ready. In practice, the user spends 5-10
seconds reading the UI, selecting options, or typing -- so the session is often ready
before the first message.

### Cache Architecture

Three singleton caches avoid re-parsing the 82+ HOCON manifest files:

```python
_systems_cache        # List of available agent network names
_factory_cache        # AgentSessionFactory (for creating chat sessions)
_direct_factory_cache # DirectAgentSessionFactory (for connectivity queries)
```

All three are warmed on server startup via `asyncio.get_event_loop().run_in_executor()`.

### Connectivity Endpoint

`GET /api/connectivity/{agent_network:path}` returns the **merged** call graph:

1. Fetches CRUSE orchestrator topology (`cruse`, `domain_expert`, `widget_generator`,
   `template_provider`)
2. Fetches target network topology (e.g., `announcer`, `synonymizer`)
3. Links them: `domain_expert` -> target's front-man
4. Returns unified `connectivity_info[]` array

This merged graph matches the agent names that appear in real-time trace events,
enabling the live visualization to highlight the correct nodes.

---

## Frontend (Next.js)

### State Management (Zustand)

All application state lives in a single Zustand store (`cruseStore.ts`):

```typescript
interface CruseState {
  // Session
  sessionId: string | null;
  agentNetwork: string | null;
  availableSystems: string[];

  // Chat
  messages: ChatMessage[];
  isStreaming: boolean;
  streamingContent: string;
  sampleQueries: string[];

  // Widget
  widgetSchema: WidgetCardDefinition | null;
  widgetFormData: Record<string, unknown>;
  widgetSubmitted: boolean;

  // Theme
  theme: BackgroundTheme | null;

  // Debug
  debugDrawerOpen: boolean;
  debugTraceEntries: AgentTraceEntry[];
  debugLogEntries: ServerLogEntry[];

  // Network visualization
  networkDrawerOpen: boolean;
  connectivityData: ConnectivityData | null;
  connectivityLoading: boolean;

  // UI
  darkMode: boolean;
  agentActivity: AgentActivity;
}
```

### Widget Lifecycle

1. Agent response contains `gui:` block with JSON Schema
2. Backend emits `widget_schema` WebSocket event
3. Store sets `widgetSchema` -> left panel slides open (420px)
4. `SchemaForm` renders the JSON Schema using `@rjsf/mui`
5. User fills form, data accumulates in `widgetFormData`
6. User presses Send -> `InputBar` attaches `form_data` to WebSocket message
7. `widgetSubmitted` flag triggers success overlay (1.8s) in the widget's own color
8. Widget clears (`setWidgetSchema(null)`) -> panel collapses -> full-width chat

### Custom Field Widgets

Five custom RJSF widgets extend the standard form rendering:

| Widget | Trigger | Renders as |
|--------|---------|------------|
| Slider | `x-ui.widget: "slider"` | MUI Slider with min/max/step |
| Rating | `x-ui.widget: "rating"` | MUI Rating (star selector) |
| FileUpload | `x-ui.widget: "file"` | Dropzone with drag-and-drop |
| Date | `format: "date"` | MUI DatePicker via dayjs |
| MultiSelect | `type: "array"` + `items.enum` | MUI Autocomplete multi-chip |

### Theme Engine

Each agent network can define visual themes via HOCON metadata tags. The backend matches
tags to CSS-doodle patterns:

- `finance` / `banking` -> geometric grid pattern
- `airline` / `travel` -> flowing aviation lines
- `health` / `medical` -> organic dot clusters
- `technology` -> geometric tech pattern
- Default -> dark gradient (`#0f172a` to `#1e293b`)

---

## HOCON Configuration

### cruse_agent.hocon Structure

The CRUSE agent network (`registries/experimental/cruse_agent.hocon`) defines the
orchestration layer. Key sections:

```hocon
{
    include "registries/aaosa.hocon"
    include "registries/llm_config.hocon"

    "metadata": {
        "description": "Context Reactive User Experience (CRUSE)...",
        "tags": ["tool", "AAOSA"],
        "sample_queries": [...]
    },

    "tools": [
        // Front-man: cruse
        {
            "name": "cruse",
            "instructions": "You are CRUSE...",
            "tools": ["domain_expert", "widget_generator"]
        },
        // Domain expert: delegates to selected agent network
        {
            "name": "domain_expert",
            "class": "coded_tools.experimental.cruse_agent.call_agent.CallAgent",
            "args": { "selected_agent": "..." }
        },
        // Widget generator: creates JSON Schema forms
        {
            "name": "widget_generator",
            "instructions": "Analyze conversation context...",
            "tools": ["template_provider"]
        },
        // Template provider: supplies widget schemas
        {
            "name": "template_provider",
            "class": "coded_tools...widget_template_provider.WidgetTemplateProvider"
        }
    ]
}
```

### Registering in the Manifest

The CRUSE agent is registered in `registries/experimental/manifest.hocon` and included
from the top-level `registries/manifest.hocon`. It is excluded from the user-facing
network selector (since it is the orchestrator, not a target network).

### Adding New Agent Networks

Any network registered in the manifest automatically appears in the CRUSE dropdown.
CRUSE wraps it transparently -- no changes to the target network are needed. The
`domain_expert` coded tool receives the selected network path at runtime via `sly_data`.

---

## Agent Network Visualization

### How It Works

The network visualization is a full-screen SVG graph that shows the complete agent
call chain in real time:

```
  [cruse]  (front-man)
   /    \
  v      v
[domain_expert]    [widget_generator]
  |                      |
  v                      v
[announcer]        [template_provider]
  |
  v
[synonymizer]
```

### Live Tracing

When agents communicate during a chat, the visualization shows activity in real time:

1. **Trace events** arrive via WebSocket (`agent_trace` events from `DebugMessageProcessor`)
2. Each trace entry contains an `origin` field in neuro_san's dot-delimited format
   (e.g., `cruse.domain_expert.announcer.synonymizer`)
3. The `useActivityState` hook parses these origins by splitting on `.` and resolving
   each segment to a graph node ID
4. Active nodes get **pulsing glow rings** and a breathing indicator dot
5. Active edges get **traveling dots** (SVG `<animateMotion>` along bezier paths)
6. Activity decays after 3 seconds of inactivity on each node/edge

### Merged Topology

The graph shows the **merged** CRUSE + target topology. This is critical because trace
events contain agent names from both layers (e.g., `cruse`, `domain_expert` from the
orchestrator AND `announcer`, `synonymizer` from the target). Without merging, the graph
nodes would never match the trace agent names.

---

## WebSocket Protocol

### Client to Server

```json
{
  "text": "I'd like to book a flight",
  "form_data": {
    "departure": "NYC",
    "arrival": "LAX",
    "date": "2026-03-15"
  }
}
```

### Server to Client

All server events follow the same envelope:

```json
{ "type": "<event_type>", "data": <payload> }
```

| Event Type | Data Shape | Description |
|------------|------------|-------------|
| `chat_complete` | `string` | Complete assistant message |
| `widget_schema` | `WidgetCardDefinition` | JSON Schema form definition |
| `theme` | `BackgroundTheme` | Background visual theme |
| `agent_activity` | `{status, agents[]}` | Agent processing status |
| `agent_trace` | `AgentTraceEntry` | Inter-agent message trace |
| `server_log` | `ServerLogEntry` | Server log entry |
| `done` | `null` | Response cycle complete |
| `error` | `{message: string}` | Error occurred |

---

## Widget System

### JSON Schema Example

A widget definition generated by the `widget_generator` agent:

```json
{
  "title": "Flight Booking",
  "description": "Book your flight",
  "icon": "FlightTakeoff",
  "color": "#0ea5e9",
  "schema": {
    "type": "object",
    "properties": {
      "departure": {
        "type": "string",
        "title": "Departure City"
      },
      "destination": {
        "type": "string",
        "title": "Destination",
        "enum": ["LAX", "SFO", "ORD", "JFK"]
      },
      "date": {
        "type": "string",
        "title": "Travel Date",
        "format": "date"
      },
      "passengers": {
        "type": "integer",
        "title": "Passengers",
        "minimum": 1,
        "maximum": 9,
        "x-ui": { "widget": "slider" }
      }
    },
    "required": ["departure", "destination", "date"]
  }
}
```

### Supported Field Types

| Type | Schema Pattern | Rendered Widget |
|------|---------------|-----------------|
| Text | `{type: "string"}` | MUI TextField |
| Textarea | `{type: "string", "x-ui": {widget: "textarea"}}` | Multiline TextField |
| Number | `{type: "number"}` | Number input |
| Boolean | `{type: "boolean"}` | MUI Switch |
| Select | `{type: "string", enum: [...]}` | MUI Select dropdown |
| Radio | `{type: "string", enum: [...], "x-ui": {widget: "radio"}}` | Radio group |
| MultiSelect | `{type: "array", items: {enum: [...]}}` | Autocomplete multi-chip |
| Date | `{type: "string", format: "date"}` | Date picker |
| Slider | `{type: "integer", minimum, maximum, "x-ui": {widget: "slider"}}` | MUI Slider |
| Rating | `{type: "integer", "x-ui": {widget: "rating"}}` | Star rating |
| File Upload | `{type: "string", "x-ui": {widget: "file"}}` | Dropzone |

---

## Running the Application

### Prerequisites

- **Python 3.12+**
- **Node.js 18+** and **npm**
- An **LLM API key** (OpenAI, Anthropic, or Google)

### 1. Clone and Setup Python Environment

```bash
git clone https://github.com/M-Elsaied/cruse-agentic-ui.git
cd cruse-agentic-ui

# Create virtual environment
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt -r requirements-build.txt
pip install -r apps/cruse/backend/requirements.txt
```

### 2. Configure Environment

```bash
# Copy and edit .env
cp .env.example .env

# Required: set at least one LLM API key
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# GOOGLE_API_KEY=AI...
```

### 3. Start the Backend

```bash
# Set PYTHONPATH to project root
export PYTHONPATH=$(pwd)          # Linux/macOS
set PYTHONPATH=%CD%               # Windows CMD

# Start FastAPI server
uvicorn apps.cruse.backend.main:app --host 0.0.0.0 --port 5001 --log-level info
```

The backend will:

- Parse the manifest and warm caches (5-10 seconds on first start)
- Start listening on `http://localhost:5001`
- Expose REST endpoints at `/api/systems`, `/api/session`, `/api/connectivity/*`
- Accept WebSocket connections at `ws://localhost:5001/ws/chat/{session_id}`

### 4. Start the Frontend

```bash
cd apps/cruse/frontend

# Install dependencies
npm install

# Create local env file
cp .env.local.example .env.local

# Start development server
npm run dev
```

The frontend starts on `http://localhost:3000` (or `3001` if 3000 is in use).

### 5. Use the Application

1. Open `http://localhost:3000` in your browser
2. Select an agent network from the dropdown in the header
3. Wait for the session to initialize (the agent activity bar will show progress)
4. Type a message and press Enter or click Send
5. If the agent generates a form, it appears on the left -- fill it out and send
6. Click the tree icon in the header to open the live network visualization
7. Click the bug icon to open the debug trace viewer

### Docker (Alternative)

```bash
cd apps/cruse

# Set your API key
export OPENAI_API_KEY=sk-...

# Build and run
docker-compose up --build
```

This starts:

- **Backend** on `http://localhost:5001`
- **Frontend** on `http://localhost:3000`

---

## Project Structure

```
apps/cruse/
+-- interface_flask.py          # Original Flask implementation (preserved)
+-- cruse_assistant.py          # Original agent logic (reused directly)
+-- docker-compose.yml          # Docker orchestration
+-- Dockerfile.backend          # Backend container definition
+-- CRUSE_NEXT_GEN.md           # This documentation
+-- backend/
|   +-- main.py                 # FastAPI app + endpoints
|   +-- session_manager.py      # Multi-session + connectivity
|   +-- streaming_bridge.py     # Async bridge to sync agent calls
|   +-- response_parser.py      # say:/gui: block parser
|   +-- theme_service.py        # HOCON metadata -> visual themes
|   +-- session_store.py        # Session timeout cleanup
|   +-- debug_message_processor.py  # Agent trace capture
|   +-- log_capture.py          # Server log ring buffer
|   +-- models.py               # Pydantic models
|   +-- requirements.txt        # Python deps (FastAPI, uvicorn)
+-- frontend/
    +-- package.json            # Next.js 14 + MUI 5 + RJSF
    +-- src/
        +-- app/
        |   +-- page.tsx        # Entry point
        |   +-- layout.tsx      # Root layout + theme provider
        +-- components/
        |   +-- CruseLayout.tsx
        |   +-- Header.tsx
        |   +-- InputBar.tsx
        |   +-- activity/       # Agent activity bar
        |   +-- chat/           # Chat panel + messages
        |   +-- debug/          # Debug drawer + panels
        |   +-- network/        # Network visualization
        |   |   +-- NetworkDrawer.tsx
        |   |   +-- NetworkGraph.tsx
        |   +-- theme/          # Background engine
        |   +-- tour/           # Spotlight walkthrough
        |   +-- widget/         # Widget card + schema form
        +-- hooks/
        |   +-- useWebSocket.ts
        +-- store/
        |   +-- cruseStore.ts
        +-- types/
            +-- debug.ts
            +-- network.ts
            +-- theme.ts
            +-- widget.ts

coded_tools/experimental/cruse_agent/
+-- call_agent.py               # Domain expert delegation
+-- widget_template_provider.py # Widget schema templates

registries/experimental/
+-- cruse_agent.hocon           # CRUSE agent network definition
+-- manifest.hocon              # Experimental network registry
```

---

## Future Improvements

### Performance Optimization

**Session initialization (~13s)** is the biggest pain point. The `CruseSession` creates
a full Neuro SAN agent session which involves parsing HOCON files, initializing LLM
factories, and setting up tool registries. Potential improvements:

- **Session pooling**: Pre-create a pool of sessions for popular networks so users get
  instant responses. Recycle sessions after idle timeout.
- **Lazy tool loading**: Defer tool registry initialization until a tool is actually
  called, rather than loading everything upfront.
- **gRPC connection mode**: Use the Neuro SAN server in HTTP/gRPC mode instead of
  direct mode. The server keeps sessions warm and can serve multiple clients.
- **Response streaming**: Currently the full response is buffered before parsing.
  Implementing true token-level streaming (using `chat_token` events) would show
  partial responses as they generate.
- **Connectivity caching**: Cache the merged connectivity result per network so
  repeated drawer opens are instant.

### Widget System Enhancements

- **Conditional fields**: Support JSON Schema `if/then/else` and `dependencies` so
  fields appear/disappear based on other field values.
- **Multi-step wizards**: Allow widgets to define multiple pages/steps with navigation,
  rather than showing all fields at once.
- **Validation messages**: Display custom validation errors from the agent, not just
  JSON Schema validation (e.g., "That flight is sold out").
- **Widget persistence**: Save partially-filled forms across page refreshes using
  `localStorage` or `sessionStorage`.
- **Rich field types**: Add support for color pickers, time pickers, address
  autocomplete, phone number formatting, and currency inputs.

### User-Level Personalization

- **User profiles**: Store user preferences (dark mode, preferred networks, form
  defaults) in a backend database keyed by user ID.
- **Conversation history**: Persist chat history across sessions so users can
  resume where they left off.
- **Favorite networks**: Allow users to pin frequently-used agent networks to the
  top of the selector dropdown.
- **Custom themes**: Let users choose or create their own background themes rather
  than relying solely on network metadata tags.
- **Accessibility**: Add keyboard navigation, screen reader support, high-contrast
  mode, and reduced motion options.

### Cloud Deployment

- **Container orchestration**: Deploy with Kubernetes (Helm chart) or AWS ECS with
  auto-scaling based on active session count.
- **Load balancing**: WebSocket connections require sticky sessions. Use an
  ALB/NLB with session affinity or a Redis-backed session store.
- **Secrets management**: Move API keys from `.env` files to AWS Secrets Manager,
  GCP Secret Manager, or HashiCorp Vault.
- **CDN**: Serve the Next.js frontend from a CDN (Vercel, CloudFront) with the
  API proxied through an edge function.
- **Monitoring**: Add Prometheus metrics for session count, response latency,
  error rates, and agent token usage. Visualize with Grafana.
- **Multi-region**: For low-latency globally, deploy backend instances in multiple
  regions with a shared session store (Redis Cluster).

### Developer Experience

- **Hot reload**: Add `--reload` flag to uvicorn during development so backend
  changes take effect without manual restarts.
- **API documentation**: FastAPI auto-generates OpenAPI docs at `/docs`. Add
  detailed descriptions and examples to all endpoints.
- **E2E tests**: Add Playwright or Cypress tests that verify the full flow:
  select network -> send message -> receive widget -> submit form.
- **Storybook**: Add a Storybook instance for developing and testing UI
  components (WidgetCard, NetworkGraph, etc.) in isolation.

### Network Visualization Enhancements

- **Zoom and pan**: Add mouse wheel zoom and drag-to-pan for large networks
  with many agents.
- **Message inspection**: Click on a traveling dot or message in the ticker to
  see the full message payload in a detail panel.
- **Replay mode**: Record trace events during a conversation and replay them
  later to understand what happened step by step.
- **Performance metrics**: Show per-agent response times as node badges
  (e.g., "1.2s") to identify bottlenecks in the agent chain.
- **Export**: Allow exporting the graph as SVG or PNG for documentation or
  presentations.

---

## License

The original CRUSE implementation and all Neuro SAN Studio code are licensed under the
[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) by Cognizant Technology
Solutions Corp.

CRUSE Next-Gen additions follow the same license terms.
