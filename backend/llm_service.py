import ollama

def generate_response(message: str) -> str:
    """Non-streaming version (HTTP /chat ke liye, already bana hua)"""
    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": message}]
    )
    return response["message"]["content"]


def generate_response_stream(message: str):
    """
    Streaming version — Ollama se chunk-by-chunk response deta hai.
    Ye ek generator hai (yield use karta hai), poora response
    ek saath return nahi karta.
    """
    stream = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": message}],
        stream=True
    )
    for chunk in stream:
        content = chunk["message"]["content"]
        if content:
            yield content