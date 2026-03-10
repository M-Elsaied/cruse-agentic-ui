# CRUSE Agentic UI

<!-- pyml disable-next-line no-inline-html -->
<div align="center">

## Context Reactive User Experience - The UI Itself Is an Agent

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776ab?logo=python&logoColor=white)](https://python.org)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-000000?logo=next.js&logoColor=white)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.133-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MUI 5](https://img.shields.io/badge/MUI-5-007FFF?logo=mui&logoColor=white)](https://mui.com)
[![Neuro SAN](https://img.shields.io/badge/Neuro_SAN-0.6.35-ff6f00)](https://github.com/cognizant-ai-lab/neuro-san)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

An agentic frontend for [Neuro SAN](https://github.com/cognizant-ai-lab/neuro-san)
multi-agent networks — with dynamic AI-generated widgets, real-time agent tracing,
and interactive network visualization.

</div>

---

## Demo

<https://github.com/user-attachments/assets/8cf88c66-c8c4-42dd-972b-df086c228ab9>

---

<!-- pyml disable-next-line no-inline-html -->
<div align="center">

Dynamic Widgets — AI generates forms on the fly |
Live Tracing — Watch agents communicate in real time |
Network Graph — Interactive SVG topology

</div>

---

## Table of Contents

1. [Overview](#overview)
2. [What Changed from Upstream](#what-changed-from-upstream)
3. [Architecture](#architecture)
4. [Getting Started](#getting-started)
5. [Authentication](#authentication)
6. [Backend Deep Dive](#backend-deep-dive)
7. [Frontend Deep Dive](#frontend-deep-dive)
8. [WebSocket Protocol](#websocket-protocol)
9. [Widget System](#widget-system)
10. [Agent Network Visualization](#agent-network-visualization)
11. [Project Structure](#project-structure)
12. [Future Improvements](#future-improvements)

---

## Overview

The original **CRUSE (Context Reactive User Experience)** was created by the
**Cognizant AI Lab** team as part of
[Neuro SAN Studio](https://github.com/cognizant-ai-lab/neuro-san-studio). It introduced
the idea of an agentic UI layer that wraps any Neuro SAN agent network with a
context-reactive interface — the UI itself is an agent that decides what forms to show.

**CRUSE Agentic UI** is a rebuild that changes both the agent brain and the delivery stack:

- **Agent architecture**: Redesigned from a 2-agent monolith to a 4-agent
  separation-of-concerns chain with dedicated widget generation
- **Backend**: New FastAPI + WebSocket server replacing Flask + SocketIO
- **Frontend**: New Next.js 14 + MUI 5 + Zustand app replacing the Jinja template UI
- **Widget format**: Structured JSON Schema replacing freeform HTML
- **Visualization**: Live SVG network graph with real-time agent tracing

The original Flask implementation remains intact for backward compatibility.

---

## What Changed from Upstream

### Agent Brain: 2 Agents to 4 Agents

The most significant change is the redesign of `registries/experimental/cruse_agent.hocon`.

**Before** — the front-man LLM did everything (domain answers + HTML form generation):

```text
cruse (front-man LLM) ──→ domain_expert (coded tool)
```

**After** — separated into distinct responsibilities:

```text
cruse (front-man LLM)
  ├──→ domain_expert (coded tool / CallAgent)
  │       └──→ target agent network (AAOSA protocol)
  └──→ widget_generator (LLM agent)         ← NEW
          └──→ template_provider (coded tool) ← NEW
```

| Agent | Type | Role |
|-------|------|------|
| `cruse` | LLM (front-man) | Orchestrates a 3-step protocol |
| `domain_expert` | Coded Tool | Delegates to the user-selected agent network via AAOSA |
| `widget_generator` | **NEW** LLM Agent | Analyzes context, decides whether to generate a JSON Schema widget |
| `template_provider` | **NEW** Coded Tool | 345-line Python tool supplying JSON Schema templates |

### HOCON Comparison

| Aspect | Original | This Repo |
|--------|----------|-----------|
| GUI output | Raw HTML (freeform) | JSON Schema (structured, validatable) |
| Widget generation | Inline in front-man prompt | Dedicated `widget_generator` + `template_provider` |
| Front-man instructions | ~15 lines, single step | Conditional; skips widget for info replies and post-submit |
| Widget skip logic | Always generates HTML | `sly_data`-driven: suppressed for info replies, duplicates, post-submit |
| Field types | Whatever HTML the LLM invents | 12 typed fields with validation |
| Icons / colors | None | Material Design Icons + hex colors per widget |

### New Coded Tool: WidgetTemplateProvider

`coded_tools/experimental/cruse_widget_agent/widget_template_provider.py` — does not exist upstream.

| Feature | Description |
|---------|-------------|
| `WIDGET_SCHEMA_TEMPLATE` | Base JSON Schema with placeholder fields for the LLM to fill |
| `WIDGET_TYPE_EXAMPLES` | 12 field patterns (text, textarea, number, select, date, slider, etc.) |
| `ICON_GUIDANCE` | 17 categories with 100+ Material Design icon names + selection principles |
| `session_context` | Exposes prior submitted fields from `sly_data` so the LLM skips already-collected fields |

### Manifest Changes

| File | Change |
|------|--------|
| `registries/experimental/manifest.hocon` | `cruse_agent.hocon: false` → `true` |
| `registries/manifest.hocon` | Added CRUSE agent entries (`public: false` — orchestrator only) |

### New Backend and Frontend

67 new files across `apps/cruse/backend/` (FastAPI) and `apps/cruse/frontend/` (Next.js).
See [Backend Deep Dive](#backend-deep-dive) and [Frontend Deep Dive](#frontend-deep-dive)
for details.

---

## Architecture

```text
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
 |  |                     |      |  | parse say: / gui:|      |      |
 |  |  MUI + Framer       |      |  +------------------+      |      |
 |  |  Motion UI          |      |                            |      |
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

**Request flow**: User sends a message via WebSocket → backend seeds `sly_data["widget_state"]`
with any submitted form data → runs `CruseSession.chat()` in a thread pool → `cruse` front-man
calls `domain_expert` (AAOSA Determine/Fulfill), then conditionally calls `widget_generator`
(suppressed for informational responses and after form submissions) → `widget_generator` calls
`template_provider` which reads `sly_data` to surface already-collected fields → backend parses
the `say:`/`gui:` response → emits typed WebSocket events (`chat_complete`, `widget_schema`,
`agent_trace`, `done`) → frontend updates store and renders.

---

## Getting Started

### Prerequisites

- **Python 3.12+** and **Node.js 20+**
- An LLM API key (OpenAI, Anthropic, or Google)

### Quick Start

```bash
# Clone
git clone https://github.com/M-Elsaied/cruse-agentic-ui.git
cd cruse-agentic-ui

# Python setup
python -m venv venv
source venv/bin/activate          # Linux/macOS
# .\venv\Scripts\activate         # Windows
pip install -r requirements.txt -r requirements-build.txt
pip install -r apps/cruse/backend/requirements.txt

# Environment
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...

# Start backend
export PYTHONPATH=$(pwd)          # Linux/macOS
# set PYTHONPATH=%CD%             # Windows CMD
uvicorn apps.cruse.backend.main:app --host 0.0.0.0 --port 5001 --log-level info

# Start frontend (new terminal)
cd apps/cruse/frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open `http://localhost:3000`, select an agent network, and start chatting.

### Docker Alternative

```bash
cd apps/cruse
export OPENAI_API_KEY=sk-...
docker-compose up --build
```

Backend on `http://localhost:5001`, frontend on `http://localhost:3000`.

---

## Authentication

CRUSE uses [Clerk](https://clerk.com) for authentication with JWT-based
session tokens. Features include social login (Google, GitHub), role-based
access control, and an admin console for monitoring sessions and usage.

For the full setup guide — creating a Clerk app, configuring session tokens,
setting environment variables, and assigning admin roles — see
[docs/authentication.md](docs/authentication.md).

---

## Backend Deep Dive

### Backend Components

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app — REST + WebSocket endpoints, CORS, startup cache warming |
| `session_manager.py` | Multi-session management, eager background init, merged connectivity |
| `streaming_bridge.py` | Bridges synchronous agent calls to async WebSocket events |
| `response_parser.py` | Parses `say:`/`gui:` response blocks with JSON detection |
| `theme_service.py` | Maps HOCON metadata tags to CSS-doodle background themes |
| `session_store.py` | Session timeout cleanup (30-minute TTL) |
| `debug_message_processor.py` | Captures inter-agent trace events in real time |
| `log_capture.py` | Ring buffer (500 entries) for server log streaming |
| `models.py` | Pydantic models for the WebSocket protocol |

### Session Lifecycle

```text
POST /api/session {agent_network: "basic/hello_world"}
  → SessionManager creates CruseSession
  → Eager init starts in background thread (~13s)
  → Returns session_id immediately

WS /ws/chat/{session_id}
  → Client sends {"text": "...", "form_data": {...}}
  → Blocks until eager init completes (if still running)
  → Runs chat() in thread pool, polls debug events every 2s
  → Emits: chat_complete, widget_schema, agent_trace, done
```

### Caches

Three singletons warmed on startup to avoid re-parsing 82+ HOCON files:

```python
_systems_cache        # Available network names
_factory_cache        # AgentSessionFactory (chat sessions)
_direct_factory_cache # DirectAgentSessionFactory (connectivity queries)
```

---

## Frontend Deep Dive

### Frontend Components

| Component | Files | Purpose |
|-----------|-------|---------|
| Layout | `CruseLayout.tsx` | Flex layout — widget panel (420px) + chat + drawers |
| Header | `Header.tsx` | Network selector, new chat, dark mode, drawer toggles |
| Chat | `chat/ChatPanel.tsx`, `MessageBubble.tsx` | Markdown-rendered messages with streaming |
| Input | `InputBar.tsx` | Text input with form data attachment |
| Widget | `widget/WidgetCard.tsx`, `SchemaForm.tsx` | JSON Schema renderer with 5 custom fields |
| Network | `network/NetworkDrawer.tsx`, `NetworkGraph.tsx` | Full-screen SVG graph with live tracing |
| Debug | `debug/DebugDrawer.tsx` | Agent trace + server log panels |
| Theme | `theme/BackgroundEngine.tsx` | CSS-doodle + gradient backgrounds |
| Activity | `activity/AgentActivityBar.tsx` | Pulsing agent status pills |
| Tour | `tour/SpotlightTour.tsx` | First-use walkthrough |

### State Management

All state lives in a single Zustand store (`cruseStore.ts`) covering sessions, messages,
widgets, theme, debug traces, network visualization, and UI preferences.

### Theme Engine

Each agent network defines themes via HOCON metadata tags, mapped to CSS-doodle patterns:
`finance` → geometric grid, `airline` → flowing lines, `health` → organic dots,
`technology` → tech pattern, default → dark gradient.

---

## WebSocket Protocol

**Client → Server:**

```json
{"text": "I'd like to book a flight", "form_data": {"departure": "NYC"}}
```

**Server → Client** (all events use `{"type": "<event>", "data": <payload>}`):

| Event | Description |
|-------|-------------|
| `chat_complete` | Full assistant message text |
| `widget_schema` | JSON Schema form definition |
| `theme` | Background visual theme |
| `agent_activity` | Agent processing status |
| `agent_trace` | Inter-agent message trace |
| `server_log` | Server log entry |
| `done` | Response cycle complete |
| `error` | Error details |

---

## Widget System

The `widget_generator` agent produces JSON Schema definitions that the frontend renders
using `@rjsf/mui`. Example:

```json
{
  "title": "Flight Booking",
  "icon": "FlightTakeoff",
  "color": "#0ea5e9",
  "schema": {
    "type": "object",
    "properties": {
      "departure": {"type": "string", "title": "Departure City"},
      "destination": {"type": "string", "title": "Destination", "enum": ["LAX", "SFO", "ORD"]},
      "date": {"type": "string", "format": "date", "title": "Travel Date"},
      "passengers": {"type": "integer", "minimum": 1, "maximum": 9}
    },
    "required": ["departure", "destination", "date"]
  }
}
```

### Supported Field Types

| Type | Schema Pattern | Rendered As |
|------|---------------|-------------|
| Text | `{type: "string"}` | MUI TextField |
| Textarea | `"x-ui": {widget: "textarea"}` | Multiline TextField |
| Number | `{type: "number"}` | Number input |
| Boolean | `{type: "boolean"}` | MUI Switch |
| Select | `{enum: [...]}` | Dropdown |
| Radio | `"x-ui": {widget: "radio"}` | Radio group |
| MultiSelect | `{type: "array", items: {enum: [...]}}` | Autocomplete chips |
| Date | `{format: "date"}` | MUI DatePicker |
| Slider | `"x-ui": {widget: "slider"}` | MUI Slider |
| Rating | `"x-ui": {widget: "rating"}` | Star rating |
| File | `"x-ui": {widget: "file"}` | Drag-and-drop dropzone |

### Widget Lifecycle

1. Agent response contains `gui:` block → backend emits `widget_schema` event
2. Left panel slides open (420px) → `SchemaForm` renders the JSON Schema
3. User fills form → presses Send → `form_data` attached to next WebSocket message
4. Backend records submitted fields into `sly_data["widget_state"]` so the agent chain
   knows what was already collected and will not ask for the same fields again
5. Success overlay (1.8s) → widget clears → full-width chat resumes

---

## Agent Network Visualization

A full-screen SVG graph shows the complete agent call chain with live activity tracing.

The backend merges the CRUSE orchestrator topology with the target network topology
(`GET /api/connectivity/{network}`), linking `domain_expert` → target's front-man. This
is critical because trace events contain agent names from both layers.

### Live Tracing

When agents communicate during a chat:

1. Trace events arrive via WebSocket with dot-delimited `origin` fields
   (e.g., `cruse.domain_expert.announcer.synonymizer`)
2. Active nodes get **pulsing glow rings**
3. Active edges get **traveling dots** (SVG `<animateMotion>` along bezier paths)
4. A message ticker at the bottom shows the last 20 agent messages
5. Activity decays after 3 seconds of inactivity

---

## Project Structure

```text
apps/cruse/
├── interface_flask.py          # Original Flask app (preserved)
├── cruse_assistant.py          # Original agent logic (reused)
├── docker-compose.yml
├── Dockerfile.backend
├── backend/
│   ├── main.py                 # FastAPI app + endpoints
│   ├── session_manager.py      # Sessions + connectivity
│   ├── streaming_bridge.py     # Async bridge
│   ├── response_parser.py      # say:/gui: parser
│   ├── theme_service.py        # Tag-based themes
│   ├── session_store.py        # Timeout cleanup
│   ├── debug_message_processor.py
│   ├── log_capture.py
│   ├── models.py
│   └── requirements.txt
└── frontend/
    ├── package.json
    └── src/
        ├── app/                # Next.js entry + layout
        ├── components/
        │   ├── chat/           # Chat panel + messages
        │   ├── widget/         # Widget card + schema form + 5 custom fields
        │   ├── network/        # Network graph + drawer
        │   ├── debug/          # Debug drawer + panels
        │   ├── theme/          # Background engine
        │   ├── activity/       # Agent activity bar
        │   └── tour/           # Spotlight walkthrough
        ├── hooks/              # useWebSocket
        ├── store/              # Zustand store
        └── types/              # TypeScript definitions

coded_tools/experimental/cruse_widget_agent/
├── call_agent.py               # Domain expert (upstream)
└── widget_template_provider.py # Widget schemas + sly_data state bridge (NEW)

registries/experimental/
├── cruse_agent.hocon           # Agent network (modified)
└── manifest.hocon              # Registry (modified)
```

---

## Future Improvements

### Agentic Improvements

- **Conversation memory** — persist agent context across sessions
- **Widget learning** — track which fields users fill vs skip
- **Multi-modal input** — support image and voice attachments
- **Agent self-correction** — retry with template examples on parse failure
- **Multi-turn widgets** *(done)* — `sly_data["widget_state"]` tracks submitted fields across turns

### Performance

- **Session pooling** — pre-create sessions for popular networks
- **Response streaming** — true token-level streaming via `chat_token` events
- **Connectivity caching** — cache merged topology per network

### Widget Enhancements

- **Conditional fields** — JSON Schema `if/then/else` support
- **Multi-step wizards** — paginated form navigation
- **Rich field types** — color pickers, time pickers, currency inputs

### Personalization

- **User profiles** — persist preferences and conversation history
- **Favorite networks** — pin frequently-used networks
- **Custom themes** — user-created background themes

### Cloud Deployment

- **Kubernetes** — Helm chart with auto-scaling on session count
- **Sticky sessions** — ALB/NLB with WebSocket affinity
- **Secrets management** — AWS Secrets Manager / Vault

### Visualization Enhancements

- **Zoom and pan** — mouse wheel zoom for large networks
- **Replay mode** — record and replay trace events
- **Performance badges** — per-agent response times on nodes

---

## License

The original CRUSE implementation and all Neuro SAN Studio code are licensed under the
[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) by Cognizant Technology
Solutions Corp. CRUSE Agentic UI additions follow the same license terms.
