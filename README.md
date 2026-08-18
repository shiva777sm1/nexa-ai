# Nexa AI - Desktop AI Assistant (Foundation)

Author: Shiva
GitHub: https://github.com/Shiva777s

## Overview

This is a foundational implementation of a desktop AI assistant backend, built as part of a Software Development Internship assessment. The project focuses on real-time AI communication using a loosely-coupled LLM integration architecture.

## What's Implemented

- **FastAPI Backend** — REST + WebSocket server (`backend/main.py`)
- **LLM Integration (Ollama)** — Loosely-coupled service layer (`backend/llm_service.py`) so the provider can be swapped (e.g., to OpenAI/Anthropic) without changing route logic
- **Real-time Streaming** — WebSocket endpoint (`/ws/chat`) streams AI responses chunk-by-chunk as they're generated, instead of waiting for the full response
- **Connection Status & Auto-Reconnect** — Frontend demo client (`backend/index.html`) shows live connection status and automatically attempts reconnection on disconnect
- **Health Check Endpoint** — `/health` for monitoring

## Architecture

```
Client (WebSocket)
    ↓
FastAPI Backend (/ws/chat)
    ↓
LLM Service Layer (llm_service.py) — provider-agnostic interface
    ↓
Ollama (local LLM: llama3.2)
```

The LLM service is intentionally decoupled: `generate_response()` and `generate_response_stream()` expose a simple interface. Swapping Ollama for OpenAI/Anthropic later only requires changing this file, not the route handlers.

## Tech Stack Used

- Python 3.12+, FastAPI, WebSockets
- Ollama (local LLM runtime) — chosen for zero-cost, offline-capable development and easy demoing without API keys
- Plain HTML/JS (temporary test client — see note below)

## Not Yet Implemented (Time-Constrained)

Due to a tight delivery timeline, the following were designed/planned but not fully implemented:

- **Electron + React + TypeScript client** — currently a lightweight HTML/JS page is used to demonstrate the WebSocket streaming and connection-status behavior. The plan is to port this logic into an Electron+React+TS app using the same WebSocket contract.
- **PostgreSQL persistence** — planned schema: `users(id, email, password_hash, created_at)` and `conversations(id, user_id, title, created_at)` + `messages(id, conversation_id, role, content, created_at)`, so conversations persist across restarts and support history retrieval.
- **Redis** — planned use for (a) rate-limiting per user on `/ws/chat` to enforce fair usage, and (b) caching active session/connection state to support multiple simultaneous desktop clients per user.
- **Authentication** — planned JWT-based auth: `/register` and `/login` endpoints issuing short-lived access tokens, validated on WebSocket connect.
- **Docker Compose** — planned to containerize FastAPI backend + PostgreSQL + Redis for one-command local setup.
- **Multiple simultaneous sessions** — with Redis-backed session tracking, multiple WebSocket connections per user_id would be tracked and broadcast to accordingly.

## How to Run (Current State)

1. Install Ollama and pull a model:
   ```
   ollama pull llama3.2
   ```
2. Set up Python environment:
   ```
   cd backend
   pip install -r requirements.txt
   ```
3. Start the server:
   ```
   uvicorn main:app --reload
   ```
4. Open `backend/index.html` in a browser to test the chat interface.

## Why These Design Choices

- **WebSocket over HTTP polling**: The assessment requires real-time streamed responses; WebSockets keep a persistent connection, avoiding repeated HTTP overhead and enabling true token-by-token streaming.
- **Ollama for local development**: Avoids API costs and key management during development; the loosely-coupled service layer means production deployment could swap in a hosted LLM provider with minimal code change.
- **Async FastAPI**: Ensures the server can handle multiple concurrent WebSocket connections without blocking on any single client's LLM generation.

## Honest Note

This submission reflects a focused, time-boxed effort. The core real-time AI communication pipeline (the most technically demanding part) is fully functional. The remaining pieces (persistence, auth, containerization, native desktop client) are architected and documented above, and I'm happy to walk through the implementation plan for each during the interview.