# Aria — AI Business Operations Assistant

> An internal Copilot that connects to a company's tools, answers questions from their knowledge base, and executes multi-step tasks via AI agents.

**Status:** Phase 4 Complete  
**Last Updated:** 2026-05-07  
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
| LLM | Claude API (Anthropic) | claude-haiku-4-5 with prompt caching for cost efficiency |
| Agent Framework | LangGraph | Graph-based agent loops — current 2025 standard |
| RAG / Chains | LangChain | Document loading, chunking, retrieval |
| Vector Database | ChromaDB (local dev) → Pinecone (prod) | Semantic search over knowledge base |
| Embeddings | SentenceTransformer (all-MiniLM-L6-v2) | Local, no API cost |
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

### Phase 1 — Foundation ✅
**Goal:** Working chat app with streaming Claude responses

- [x] Initialize Next.js 14 project (App Router, TypeScript, Tailwind, shadcn/ui)
- [x] Initialize FastAPI backend with project structure
- [x] Build basic chat UI (message thread, input box, send button)
- [x] Connect frontend → FastAPI → Claude API with SSE streaming

**Deliverable:** Live chat with Claude, messages stream in real-time.

---

### Phase 2 — RAG Pipeline ✅
**Goal:** Users can upload documents and ask questions with cited answers

- [x] Document ingestion endpoint (PDF, TXT, Markdown)
- [x] Chunking strategy (recursive character splitter)
- [x] Embedding generation (SentenceTransformer all-MiniLM-L6-v2, local)
- [x] ChromaDB vector store with persistent storage
- [x] Retrieval-Augmented Generation chain (LangChain)
- [x] Knowledge Base manager UI (upload, list docs)

**Deliverable:** Upload a document, ask questions, get answers sourced from the file.

---

### Phase 3 — LangGraph Agents ✅
**Goal:** Multi-step autonomous task execution with visible reasoning

- [x] LangGraph agent with MessagesState (tool_use/tool_result pairing)
- [x] Tools: KB search, calculator
- [x] Stream agent thought steps (tool_call, tool_result, final_answer) via SSE
- [x] Agent Trace Viewer in UI (expandable reasoning steps)
- [x] Conversation history passed through agent on each turn

**Deliverable:** Ask multi-step questions — watch the agent pick tools, execute, and synthesize answers step-by-step in the UI.

---

### Phase 4 — MCP Integration ✅
**Goal:** Extensible tool system via Model Context Protocol

- [x] Notion MCP server (stdio transport) with 4 tools: query_database, search_docs, get_page, create_page
- [x] Database registry for tasks, projects, meetings, docs with exact property mappings
- [x] Smart filter builder: status, priority, stage, date ranges (this_week, today, overdue, past)
- [x] MCP client in FastAPI wraps server tools as LangChain tools, plugged into LangGraph agent
- [x] Error handling: Notion API errors returned as structured JSON so agent can self-correct
- [x] Principles-based system prompt — routes intelligently without hardcoded patterns

**Deliverable:** Ask "what are my high priority tasks this week?" or "which projects are in progress?" — agent queries live Notion data via MCP and answers.

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
2. **Prompt caching** — Claude API caches the system prompt, reducing cost by ~90% on cache hits for repeated sessions
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
| 2026-04-23 | Switched to Claude API (claude-haiku-4-5) with prompt caching | Phase 1 |
| 2026-04-28 | Phase 2 complete — RAG pipeline with ChromaDB + SentenceTransformer embeddings | Phase 2 |
| 2026-05-01 | Phase 3 complete — LangGraph agent with streaming tool traces in UI | Phase 3 |
| 2026-05-07 | Phase 4 complete — Notion MCP server with smart query routing and filter builder | Phase 4 |
