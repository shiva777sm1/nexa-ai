"""
LLM Service - Ollama Integration
Author: Shiva
"""

import ollama


def generate_response(message: str) -> str:
    """Non-streaming version (HTTP /chat ke liye) - single message, no history"""
    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": message}]
    )
    return response["message"]["content"]


def generate_response_with_history(history: list) -> str:
    """
    Non-streaming version JISME poori conversation history bheji jaati hai.
    history format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
    """
    response = ollama.chat(
        model="llama3.2",
        messages=history
    )
    return response["message"]["content"]


def generate_response_stream(message: str):
    """Streaming version - single message, no history (backward compatible)"""
    stream = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": message}],
        stream=True
    )
    for chunk in stream:
        content = chunk["message"]["content"]
        if content:
            yield content


def generate_response_stream_with_history(history: list):
    """
    Streaming version JISME poori conversation history bheji jaati hai.
    Ye WebSocket chat ke liye use hoga, taaki AI ko context yaad rahe.
    """
    stream = ollama.chat(
        model="llama3.2",
        messages=history,
        stream=True
    )
    for chunk in stream:
        content = chunk["message"]["content"]
        if content:
            yield content