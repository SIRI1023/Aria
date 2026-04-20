# Aria — AI Business Operations Assistant

> An internal Copilot that connects to your company's tools, answers questions from your knowledge base, and executes multi-step tasks via AI agents.

---

## What It Does

- **Chat with your knowledge base** — upload documents, get cited answers
- **Autonomous task execution** — multi-step agent that plans, searches, and synthesizes
- **Extensible tool system** — connect any tool via MCP (Model Context Protocol)
- **Real-time reasoning** — watch the agent think step-by-step in the UI

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router, TypeScript, Tailwind CSS, shadcn/ui) |
| Backend | Python FastAPI |
| LLM | Claude API (Anthropic) with prompt caching |
| Agent Framework | LangGraph |
| RAG / Chains | LangChain + ChromaDB |
| Embeddings | OpenAI text-embedding-3-small |
| Database | Supabase (PostgreSQL + Auth) |
| Protocol | MCP (Model Context Protocol) |
| Streaming | Server-Sent Events (SSE) |

---

## Project Structure

```
aria/
├── backend/                ← FastAPI app
│   ├── app/
│   │   ├── api/routes/     ← HTTP endpoints
│   │   ├── services/       ← Claude API, RAG, agents
│   │   └── core/           ← Config, settings
│   └── main.py
└── frontend/               ← Next.js 14 app
    └── src/
        ├── app/            ← Pages (App Router)
        ├── components/     ← Chat UI components
        └── lib/            ← API client, utilities
```

---

## Build Phases

- **Phase 1** — Streaming chat with Claude API ✅
- **Phase 2** — RAG pipeline: document ingestion, ChromaDB, cited answers
- **Phase 3** — LangGraph agents with visible reasoning traces
- **Phase 4** — MCP custom servers + multi-tenant workspaces

---

## Local Setup

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env       # add your API keys
uvicorn main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open `http://localhost:3000`

---

## Author

Built by [sriGovvala](https://github.com/SIRI1023) as a portfolio project demonstrating LLM application engineering, RAG pipelines, and agent orchestration.
