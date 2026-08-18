from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from llm_service import generate_response, generate_response_stream

app = FastAPI()

@app.get("/")
def home():
    return {"message": "nexa ai is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(request: ChatRequest):
    reply = generate_response(request.message)
    return {"reply": reply}


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")

    try:
        while True:
            # Client se message receive karo
            data = await websocket.receive_text()
            print(f"Received: {data}")

            # Ollama se streaming response lo, chunk-by-chunk bhejo
            for chunk in generate_response_stream(data):
                await websocket.send_text(chunk)

            # Signal ki response complete ho gaya
            await websocket.send_text("[END]")

    except WebSocketDisconnect:
        print("Client disconnected")