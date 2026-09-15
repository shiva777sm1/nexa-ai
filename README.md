# Nexa AI — Desktop AI Assistant
 
A production-style desktop AI assistant built as the foundation for a real-time, multi-session, persistent chat application. Built with a full modern stack: Electron, React, TypeScript, FastAPI, PostgreSQL, Redis, and Docker.
 
**Author:** Shiva
**GitHub:** https://github.com/Shiva777s
 
---
 
## Features
 
- **Authentication** — Secure registration and login using hashed passwords (bcrypt) and JWT-based session tokens.
- **Real-Time Streaming** — AI responses stream token-by-token over WebSockets instead of waiting for a full response.
- **Conversation Memory** — Each conversation's full message history is persisted and replayed to the model, so the assistant retains context across turns.
- **Persistence** — PostgreSQL stores users, conversations, and messages, so nothing is lost on restart.
- **Rate Limiting** — Redis enforces a per-user request limit to prevent excessive resource consumption.
- **Desktop Client** — A native Electron application (not just a browser tab) with a polished, custom-designed interface.
- **Connection Resilience** — The client detects disconnects and automatically attempts to reconnect.
- **Provider-Agnostic AI Layer** — The LLM integration is isolated behind a small service layer, so swapping the underlying model/provider (e.g., moving from a local Ollama model to a hosted API) requires no changes to route logic.
- **Containerized Backend** — PostgreSQL, Redis, and the FastAPI backend run together via Docker Compose with a single command.
## Tech Stack
 
| Layer | Technology |
|---|---|
| Desktop Shell | Electron |
| Frontend | React + TypeScript (Vite) |
| Backend | Python 3.12, FastAPI |
| Real-Time Transport | WebSockets |
| Database | PostgreSQL (via SQLAlchemy ORM) |
| Cache / Rate Limiting | Redis |
| AI Model | Ollama (local LLM runtime) |
| Containerization | Docker & Docker Compose |
| Auth | JWT (python-jose) + bcrypt password hashing |
 
## Architecture
 
```
Electron Desktop App (React + TypeScript)
        │  WebSocket + REST
        ▼
FastAPI Backend
   ├── Auth Service (JWT, bcrypt)
   ├── Rate Limiter (Redis)
   ├── LLM Service (provider-agnostic → Ollama)
   └── Persistence Layer (SQLAlchemy → PostgreSQL)
```
 
The LLM service exposes a simple `generate_response_stream_with_history()` interface. Everything above that layer — routes, WebSocket handling, persistence — is unaware of which model or provider is actually generating the response.
 
## Project Structure
 
```
nexa-ai/
├── backend/
│   ├── main.py              # FastAPI app, routes, WebSocket handler
│   ├── models.py            # SQLAlchemy models (User, Conversation, Message)
│   ├── database.py          # DB engine/session setup
│   ├── auth.py               # Password hashing + JWT logic
│   ├── llm_service.py        # Ollama integration (streaming + history)
│   ├── rate_limiter.py       # Redis-based rate limiting
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # Main chat + auth UI
│   │   └── index.css
│   └── electron/
│       └── main.cjs          # Electron main process
├── docker-compose.yml         # Orchestrates Postgres + Redis + Backend
└── README.md
```
 
## Getting Started
 
### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Node.js](https://nodejs.org/) (v18+)
- [Ollama](https://ollama.com/) installed locally, with a model pulled:
```
  ollama pull llama3.2
```
 
### 1. Start the backend stack (PostgreSQL + Redis + FastAPI)
```bash
docker-compose up --build
```
This starts the database, cache, and API together. The API will be available at `http://localhost:8000`.
 
### 2. Start the desktop client
```bash
cd frontend
npm install
npm run electron:dev
```
This launches the Electron window, which connects to the backend automatically.
 
## Design Decisions
 
- **WebSockets over polling** — the assessment/use-case requires real-time streamed responses; a persistent connection avoids repeated HTTP overhead and enables true token-by-token delivery.
- **Ollama for local development** — avoids API costs and key management while building; the provider-agnostic service layer means a hosted LLM API could be substituted with a small, isolated code change.
- **Redis for rate limiting** — an in-memory store with built-in key expiry is a natural fit for sliding time-window request limits, and it's already the standard tool for this job in production systems.
- **JWT over server-side sessions** — keeps the backend stateless and makes it straightforward to authenticate both REST requests and WebSocket connections using the same token.
## Known Limitations / Next Steps
 
- Multiple simultaneous sessions per user are not yet explicitly tracked/broadcast — each WebSocket connection currently operates independently.
- The Electron build is currently configured for development; a packaged installer (via `electron-builder`) is the next step for distribution.
