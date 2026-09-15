"""
Nexa AI - Desktop AI Assistant Backend
 
FastAPI application exposing authentication, chat, and real-time
WebSocket streaming endpoints for the Nexa AI desktop client.
 
Author: Shiva
GitHub: https://github.com/Shiva777s
"""
 
import logging
 
from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
 
from auth import create_access_token, decode_access_token, hash_password, verify_password
from database import Base, engine, get_db
from llm_service import generate_response, generate_response_stream_with_history
from models import Conversation, Message, User
from rate_limiter import is_rate_limited
 
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("nexa_ai")
 
Base.metadata.create_all(bind=engine)
 
app = FastAPI(title="Nexa AI", version="0.1.0")
 
# Allows the Electron/React frontend (running on Vite's dev server) to call
# this API. Browsers block cross-origin requests by default, so this is
# required for local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
 
# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------
 
class ChatRequest(BaseModel):
    message: str
 
 
class RegisterRequest(BaseModel):
    email: str
    password: str
 
 
class LoginRequest(BaseModel):
    email: str
    password: str
 
 
# --------------------------------------------------------------------------
# Auth dependency
# --------------------------------------------------------------------------
 
def get_current_user(authorization: str = Header(...), db: Session = Depends(get_db)) -> User:
    """Resolve the authenticated user from a Bearer token.
 
    Raises a 401 if the token is missing, invalid, expired, or no longer
    matches an existing user.
    """
    try:
        token = authorization.replace("Bearer ", "")
        payload = decode_access_token(token)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
 
        user = db.query(User).filter(User.id == payload["user_id"]).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
 
        return user
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Authentication failed") from exc
 
 
# --------------------------------------------------------------------------
# Health
# --------------------------------------------------------------------------
 
@app.get("/")
def home():
    return {"message": "nexa ai is running"}
 
 
@app.get("/health")
def health():
    return {"status": "healthy"}
 
 
# --------------------------------------------------------------------------
# Auth routes
# --------------------------------------------------------------------------
 
@app.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        return {"error": "Email already registered"}
 
    new_user = User(email=request.email, password_hash=hash_password(request.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
 
    return {"message": "User registered successfully", "user_id": new_user.id}
 
 
@app.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
 
    if not user or not verify_password(request.password, user.password_hash):
        return {"error": "Invalid email or password"}
 
    token = create_access_token(data={"user_id": user.id, "email": user.email})
    return {"access_token": token, "token_type": "bearer"}
 
 
# --------------------------------------------------------------------------
# Chat routes
# --------------------------------------------------------------------------
 
@app.post("/chat")
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Single-turn HTTP chat endpoint. Persists the exchange as a new
    conversation. Primarily useful for quick testing; the WebSocket
    endpoint is the real-time, stateful chat interface used by the client.
    """
    if is_rate_limited(current_user.id):
        return {"error": "Too many requests. Please wait a moment before sending another message."}
 
    conversation = Conversation(user_id=current_user.id, title=request.message[:30])
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
 
    db.add(Message(conversation_id=conversation.id, role="user", content=request.message))
    db.commit()
 
    reply = generate_response(request.message)
 
    db.add(Message(conversation_id=conversation.id, role="assistant", content=reply))
    db.commit()
 
    return {"reply": reply, "conversation_id": conversation.id}
 
 
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """Real-time chat endpoint. Authenticates via a `token` query parameter
    (WebSocket connections can't carry custom headers the way REST clients
    can), then streams model responses back to the client chunk by chunk
    while persisting the full conversation history.
    """
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return
 
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=1008, reason="Invalid or expired token")
        return
 
    db = next(get_db())
    user = db.query(User).filter(User.id == payload["user_id"]).first()
 
    if user is None:
        await websocket.close(code=1008, reason="User not found")
        db.close()
        return
 
    await websocket.accept()
    logger.info("Client connected: %s", user.email)
 
    conversation = Conversation(user_id=user.id, title="WebSocket Chat")
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
 
    try:
        while True:
            data = await websocket.receive_text()
 
            if is_rate_limited(user.id):
                await websocket.send_text("Rate limit exceeded. Please wait a moment before sending more messages.")
                await websocket.send_text("[END]")
                continue
 
            db.add(Message(conversation_id=conversation.id, role="user", content=data))
            db.commit()
 
            # Replay the full conversation so the model retains context
            # across turns.
            past_messages = (
                db.query(Message)
                .filter(Message.conversation_id == conversation.id)
                .order_by(Message.created_at)
                .all()
            )
            history = [{"role": m.role, "content": m.content} for m in past_messages]
 
            full_reply = ""
            try:
                for chunk in generate_response_stream_with_history(history):
                    full_reply += chunk
                    await websocket.send_text(chunk)
            except Exception:
                logger.info("Client disconnected mid-stream: %s", user.email)
                break
 
            await websocket.send_text("[END]")
 
            db.add(Message(conversation_id=conversation.id, role="assistant", content=full_reply))
            db.commit()
 
    except WebSocketDisconnect:
        logger.info("Client disconnected: %s", user.email)
    finally:
        db.close()
