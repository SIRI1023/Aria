# Aria — AI Business Operations Assistant

> An internal Copilot that connects to a company's tools, answers questions from their knowledge base, and executes multi-step tasks via AI agents.

**Status:** Planning  
**Last Updated:** 2026-04-17  
**Owner:** shri.govvala@gmail.com

---

## Vision

Business users waste hours searching across Notion, Google Drive, Slack, and databases to find answers and compile reports. Aria gives them a single AI-powered interface to:

- Ask questions and get answers **with citations** from their connected knowledge base
- **Execute multi-step tasks** autonomously (e.g., "summarize last week's support tickets and draft a report")
- **Connect any tool** via the MCP protocol — without writing custom integrations every time
- Watch the agent **reason in real-time** so users trust and understand the output

---

## Target Roles This Project Demonstrates

| Role | What Aria Proves |
|---|---|
| Full-Stack Engineer (AI-adjacent) | Next.js 14 + Python FastAPI + streaming UI |
| Integration / Middleware Engineer | MCP servers, multi-source connectors, multi-tenant architecture |
| LLM / AI Application Engineer | RAG pipeline, vector DB, LangGraph agents, prompt caching |

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Frontend | Next.js 14 (App Router) | Industry standard for AI product UIs |
| UI Components | Tailwind CSS + shadcn/ui | Fast, clean, professional |
| Backend | Python FastAPI | Standard for LLM backends |
| LLM | Claude API (Anthropic) | With prompt caching for cost efficiency |
| Agent Framework | LangGraph | Graph-based agent loops — current 2025 standard |
| RAG / Chains | LangChain | Document loading, chunking, retrieval |
| Vector Database | ChromaDB (local dev) → Pinecone (prod) | Semantic search over knowledge base |
| Embeddings | OpenAI text-embedding-3-small | Vendor-agnostic, can swap |
| Database | Supabase (PostgreSQL + Auth) | Multi-tenant user/workspace data |
| Protocol | MCP (Model Context Protocol) | Custom servers for tool extensibility |
| Streaming | Server-Sent Events (SSE) | Real-time agent reasoning in the UI |
| Deployment | Vercel (frontend) + Railway (backend) | Fast, zero-ops |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  Next.js Frontend                    │
│   Chat UI  │  Agent Trace Viewer  │  KB Manager      │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP + SSE
┌─────────────────────▼───────────────────────────────┐
│                 FastAPI Backend                       │
│                                                      │
│   ┌──────────────┐    ┌────────────────────────┐    │
│   │  RAG Service │    │   LangGraph Agent       │    │
│   │              │    │                        │    │
│   │  Ingest docs │    │  Plan → Search KB      │    │
│   │  Chunk+embed │    │  → Call Tools → Answer │    │
│   │  ChromaDB    │    │                        │    │
│   └──────────────┘    └──────────┬─────────────┘    │
│                                  │                   │
│   ┌───────────────────────────────▼───────────────┐  │
│   │              MCP Tool Registry                │  │
│   │  Notion MCP │ Google Drive MCP │ Custom DBs   │  │
│   └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│                   Supabase                           │
│   Users │ Workspaces │ Conversations │ Documents     │
└─────────────────────────────────────────────────────┘
```

---

## Build Phases

### Phase 1 — Foundation (Week 1–2)
**Goal:** Working chat app with streaming Claude responses

- [ ] Initialize Next.js 14 project (App Router, TypeScript, Tailwind, shadcn/ui)
- [ ] Initialize FastAPI backend with project structure
- [ ] Set up Supabase project (auth + database schema)
- [ ] Implement Next.js auth (sign up, login, protected routes)
- [ ] Build basic chat UI (message thread, input box, send button)
- [ ] Connect frontend → FastAPI → Claude API with SSE streaming
- [ ] Deploy: Vercel + Railway

**Deliverable:** Live URL where you can chat with Claude, messages stream in real-time, auth works.

---

### Phase 2 — RAG Pipeline (Week 3–4)
**Goal:** Users can upload documents and ask questions with cited answers

- [ ] Document ingestion endpoint (PDF, TXT, Markdown)
- [ ] Chunking strategy (recursive character splitter)
- [ ] Embedding generation (OpenAI text-embedding-3-small)
- [ ] ChromaDB setup with per-workspace collections (multi-tenant)
- [ ] Retrieval-Augmented Generation chain (LangChain)
- [ ] Citations in responses (show source document + chunk)
- [ ] Knowledge Base manager UI (upload, list, delete docs)

**Deliverable:** Upload a PDF, ask "what does this say about X?" and get a cited answer.

---

### Phase 3 — LangGraph Agents (Week 5–6)
**Goal:** Multi-step autonomous task execution with visible reasoning

- [ ] Design agent graph (Planner → Tool Selector → Executor → Synthesizer)
- [ ] Implement tools: KB search, web search (Tavily), doc generator
- [ ] Stream agent "thought steps" to frontend via SSE
- [ ] Build Agent Trace Viewer in UI (collapsible reasoning steps)
- [ ] Implement agent memory (conversation history in Supabase)
- [ ] Add guardrails (max steps, timeout, fallback to direct answer)

**Deliverable:** Ask "summarize my uploaded docs and create a bullet-point brief" — watch the agent plan and execute it step-by-step in the UI.

---

### Phase 4 — MCP Integration (Week 7–8)
**Goal:** Extensible tool system via Model Context Protocol

- [ ] Build a custom MCP server (Notion connector as first target)
- [ ] MCP server registry in FastAPI (register/list/call tools)
- [ ] Plug MCP tools into LangGraph agent's tool registry
- [ ] Build "Connect a Tool" UI (list available MCP servers, enable/disable)
- [ ] Multi-tenant workspace settings (each workspace has its own tool config)
- [ ] Write a second MCP server (Google Drive or custom SQL query)

**Deliverable:** Connect Notion, ask "what are my open action items from last week's meeting notes?" — agent reads Notion via MCP and answers.

---

## Database Schema (Supabase)

```sql
-- Multi-tenant foundation
workspaces (id, name, owner_id, created_at)
workspace_members (workspace_id, user_id, role)

-- Knowledge base
documents (id, workspace_id, name, source_url, status, created_at)
document_chunks (id, document_id, content, embedding_id, metadata)

-- Conversations
conversations (id, workspace_id, user_id, title, created_at)
messages (id, conversation_id, role, content, agent_trace, created_at)

-- MCP / Tools
mcp_servers (id, workspace_id, name, server_url, config, enabled)
```

---

## Key Interview Talking Points

1. **LangGraph over plain LangChain agents** — explain why graph-based agents handle cycles, retries, and conditional routing better than the legacy AgentExecutor
2. **Prompt caching** — Claude API caches the system prompt + KB context, reducing cost by ~80% on repeat queries in the same session
3. **Multi-tenant vector isolation** — each workspace gets its own ChromaDB collection; embeddings never cross workspace boundaries
4. **MCP as an abstraction layer** — instead of hardcoding every integration, MCP gives you a standard protocol, so adding a new tool is a 1-day task not a 2-week project
5. **Streaming agent traces** — users see the agent's reasoning; this builds trust and is a key differentiator for enterprise adoption

---

## Folder Structure (planned)

```
aria/
├── PROJECT.md              ← this file
├── frontend/               ← Next.js 14 app
│   ├── app/
│   ├── components/
│   └── lib/
├── backend/                ← FastAPI app
│   ├── app/
│   │   ├── api/            ← route handlers
│   │   ├── agents/         ← LangGraph definitions
│   │   ├── rag/            ← ingestion + retrieval
│   │   ├── mcp/            ← MCP server registry + clients
│   │   └── db/             ← Supabase client + queries
│   └── main.py
├── mcp-servers/            ← custom MCP server implementations
│   └── notion/
└── docs/                   ← architecture diagrams, ADRs
```

---

## Change Log

| Date | Change | Phase |
|---|---|---|
| 2026-04-17 | Initial project documentation created | Planning |
| 2026-04-20 | Phase 1 complete — FastAPI backend + Next.js chat UI with SSE streaming | Phase 1 |
