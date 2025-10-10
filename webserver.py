from fastapi import FastAPI, Request, Depends, Header, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from typing import List, Dict, Any
import os
import logging
from dotenv import load_dotenv
from requests import HTTPError

# Load environment variables from .env at project root
load_dotenv()

# Qwen (OpenRouter) provider only
from src.providers.qwen_provider import QwenProvider

app = FastAPI(title="Qwen Chatbot Server (Qwen-only)")

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
    system_prompt = (data.get("system_prompt") or "").strip()

    if not messages:
        messages = [{"role": "user", "content": "Hello"}]

    if system_prompt:
        messages = [{"role": "system", "content": system_prompt}] + messages

    try:
        provider = QwenProvider()
        reply = provider.chat(messages)
        return JSONResponse({"reply": reply})
    except HTTPError as he:
        status = getattr(he.response, "status_code", None) or 502
        msg = f"OpenRouter HTTPError {status}: {he}"
        logging.exception(msg)
        raise HTTPException(status_code=status, detail=msg)
    except Exception as e:
        msg = f"Chat failed: {e}"
        logging.exception(msg)
        raise HTTPException(status_code=500, detail=msg)


@app.get("/api/health", dependencies=[Depends(require_auth)])
def health():
    ok = bool(os.getenv("OPENROUTER_API_KEY"))
    return {"ok": ok}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
