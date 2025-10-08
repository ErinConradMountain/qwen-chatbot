from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi import Depends, Header, HTTPException
from fastapi.staticfiles import StaticFiles
import uvicorn
from typing import List, Dict, Any
import json, os, requests

# Reuse existing config and provider
from src.providers.qwen_provider import QwenProvider
from providers.ollama import OllamaProvider
from core.stream import normalize_openai_sse, normalize_ollama_ndjson

app = FastAPI(title="Qwen Chatbot Server")

app.mount("/web", StaticFiles(directory="web"), name="web")


def require_auth(x_auth_token: str | None = Header(default=None, alias="X-Auth-Token")):
    expected = os.getenv("CHATKIT_AUTH_TOKEN")
    if expected and x_auth_token != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Auth-Token")


@app.get("/")
async def root_index():
    return FileResponse("web/index.html")


@app.post("/api/chat/qwen", dependencies=[Depends(require_auth)])
async def api_chat_qwen(req: Request):
    data = await req.json()
    messages: List[Dict[str, Any]] = data.get("messages", [])
    model = data.get("model")

    # Ensure messages minimally include a system prompt if provider expects
    if not messages:
        messages = [{"role": "user", "content": "Hello"}]

    # StreamingResponse (concatenate then send). Real SSE chunking can be added later.
    def generate():
        provider = QwenProvider()
        text = provider.chat(messages, model_override=model) if model else provider.chat(messages)
        yield text

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@app.post("/api/chat/ollama", dependencies=[Depends(require_auth)])
async def api_chat_ollama(req: Request):
    data = await req.json()
    messages: List[Dict[str, Any]] = data.get("messages", [])
    model = data.get("model")

    provider = OllamaProvider()

    async def stream():
        # Use Ollama /api/generate stream=true with concatenated prompt from messages
        # Fall back to /api/chat non-stream if needed (handled in provider)
        with provider.stream_generate(messages, model_override=model) as resp:
            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    d = normalize_ollama_ndjson(obj)
                    if d and d.text:
                        yield d.text
                except Exception:
                    # If a non-JSON line slips through, just forward raw
                    yield line.decode("utf-8", errors="ignore")

    return StreamingResponse(stream(), media_type="text/plain; charset=utf-8")


@app.post("/api/llm/stream", dependencies=[Depends(require_auth)])
async def api_llm_stream(req: Request):
    """Unified OpenAI-compatible streaming proxy. Expects messages + model.
    Defaults to LiteLLM at http://localhost:4000/v1/chat/completions.
    """
    data = await req.json()
    messages = data.get("messages", [])
    model = data.get("model", "qwen-stream")
    base = os.getenv("LITELLM_BASE_URL", "http://127.0.0.1:4000")
    url = f"{base}/v1/chat/completions"
    payload = {"model": model, "messages": messages, "stream": True}
    headers = {"Content-Type": "application/json"}
    # Optional: pass through OpenAI-style api key if set
    api_key = os.getenv("LITELLM_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    def gen():
        with requests.post(url, json=payload, headers=headers, stream=True, timeout=0) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                # SSE lines look like: b'data: {"id":..., "choices":[{"delta":{"content":"t"}}]}'
                if line.startswith(b"data: "):
                    line = line[len(b"data: "):]
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                d = normalize_openai_sse(obj)
                if d and d.text:
                    yield d.text

    return StreamingResponse(gen(), media_type="text/plain; charset=utf-8")


@app.get("/api/health", dependencies=[Depends(require_auth)])
def health():
    ok = True
    detail = {}
    try:
        base = os.getenv("LITELLM_BASE_URL", "http://127.0.0.1:4000")
        url = f"{base}/v1/chat/completions"
        payload = {"model": "qwen-stream", "messages": [{"role": "user", "content": "hi"}], "stream": False, "max_tokens": 1}
        r = requests.post(url, json=payload, timeout=3)
        detail["litellm"] = r.status_code
    except Exception as e:
        ok = False
        detail["litellm_error"] = str(e)

    try:
        ollama = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        r2 = requests.get(f"{ollama}/api/tags", timeout=3)
        detail["ollama"] = r2.status_code
    except Exception as e:
        ok = False
        detail["ollama_error"] = str(e)

    return {"ok": ok, "detail": detail}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
