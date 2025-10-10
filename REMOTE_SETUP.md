# Remote Deployment Guide

This project is designed to run on a low-resource student machine locally (using the Qwen provider via OpenRouter) and scale up on a remote host where you can install heavier dependencies such as Ollama, LiteLLM, or vLLM.

Use this guide once you push the repo to GitHub and want to bring up a richer environment on a remote server or workstation.

## Local Development (reference)

- Install dependencies: `pip install -r requirements.txt`
- Set your OpenRouter key (PowerShell):
  ```powershell
  $env:OPENROUTER_API_KEY = "sk-or-..."
  ```
- Run the server: `python webserver.py`
- Open the UI: `http://127.0.0.1:8000/`
- In the sidebar choose **Provider: Qwen**, optionally set `Model = qwen/qwen3-4b:free`, click **Test Connection**, then chat.

> No Ollama installation is required locally; this keeps your machine light while you iterate.

## Remote Setup Checklist

1. **Provision a host** (cloud VM, school lab box, spare PC). Ubuntu/Debian instructions are provided below.
2. **Clone the repo** from GitHub onto the remote host.
3. **Install system dependencies** (Python, pip, curl, optional: Ollama or LiteLLM).
4. **Configure environment variables** for the mode you want (OpenRouter only, Ollama direct, or LiteLLM proxy).
5. **Start the chatbot server** (`python webserver.py` or `uvicorn webserver:app --host 0.0.0.0 --port 8000`).
6. **(Optional) Enable streaming** by running LiteLLM and pointing the server at it.
7. **Secure the deployment** if exposing beyond localhost (reverse proxy + `CHATKIT_AUTH_TOKEN`).

## Remote Bootstrap (Ubuntu/Debian example)

SSH into the remote machine and run:

```bash
sudo apt update && sudo apt install -y curl python3 python3-pip git
git clone <YOUR_FORK_OR_REPO_URL>
cd qwen-chatbot-https
pip install -r requirements.txt
```

### Option A – Qwen via OpenRouter (no heavy installs)

```bash
export OPENROUTER_API_KEY="sk-or-..."
python webserver.py  # binds to 127.0.0.1; use --host 0.0.0.0 if needed
```

Open the UI remotely (e.g., via SSH port-forwarding or reverse proxy) and choose **Provider: Qwen**.

### Option B – Direct Ollama (enable larger local models)

```bash
curl https://ollama.com/install.sh | sh
ollama serve &
ollama pull qwen2.5:7b-instruct       # pull additional models as needed (e.g., llama3:8b-instruct)
export MODEL_NAME="qwen2.5:7b-instruct"
python webserver.py
```

In the UI choose **Provider: Ollama**. Streaming is enabled automatically.

### Option C – LiteLLM Proxy (OpenAI-compatible streaming)

```bash
pip install -r requirements-dev.txt  # includes litellm[proxy]
PORT=4000 scripts/run_litellm.sh     # starts proxy on 127.0.0.1:4000
export LITELLM_BASE_URL="http://127.0.0.1:4000"
python webserver.py
```

In the UI choose **Provider: Qwen** or any alias you configure in `litellm_config.yaml`. Add more models and aliases as needed.

## Environment Variables

| Variable               | Purpose                                                       |
|------------------------|---------------------------------------------------------------|
| `OPENROUTER_API_KEY`   | Enables Qwen via OpenRouter (no local model required).        |
| `MODEL_NAME`           | Default model for Ollama (e.g., `qwen2.5:7b-instruct`).       |
| `LITELLM_BASE_URL`     | Base URL for LiteLLM proxy (`http://127.0.0.1:4000`).         |
| `LITELLM_API_KEY`      | Optional bearer token if your proxy requires authentication.  |
| `OLLAMA_BASE_URL`      | Override Ollama endpoint (`http://127.0.0.1:11434`).          |
| `CHATKIT_AUTH_TOKEN`   | If set, API routes require header `X-Auth-Token`.             |

## Running Under a Process Manager

For a production-like remote setup you can run the services under systemd, supervisord, or Docker. Example with systemd (Ollama + chatbot):

```ini
# /etc/systemd/system/ollama.service
[Unit]
Description=Ollama Service
After=network.target

[Service]
ExecStart=/usr/local/bin/ollama serve
Restart=always

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/chatbot.service
[Unit]
Description=Qwen Chatbot
After=network.target

[Service]
Environment="OPENROUTER_API_KEY=sk-or-..."
Environment="LITELLM_BASE_URL=http://127.0.0.1:4000"  # optional
WorkingDirectory=/opt/qwen-chatbot-https
ExecStart=/usr/bin/python3 webserver.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable them with `sudo systemctl enable --now ollama`, `sudo systemctl enable --now chatbot`.

## Securing Remote Access

- Bind FastAPI to `127.0.0.1` and expose via an HTTPS reverse proxy (Caddy/Nginx) or an SSH tunnel.
- Set `CHATKIT_AUTH_TOKEN` and require the header `X-Auth-Token` on all API calls.
- Consider Cloudflare Tunnels or Tailscale for private access without opening inbound ports.

## Quick Verification

1. Run `python webserver.py` (or the process manager unit).
2. Hit `/api/health` – expect status 200 for the services you enabled (OpenRouter, LiteLLM, Ollama).
3. Open the web UI (via port-forward or reverse proxy).
4. Click **Test Connection** and confirm the appropriate backends are reachable.
5. Start a new chat and send a prompt – you should receive a conversational response.

## Extending with Larger Models

- Pull extra models on the remote host: `ollama pull llama3:8b-instruct`, `ollama pull mistral:7b-instruct`, etc.
- Update `litellm_config.yaml` with new aliases if you want them accessible through the proxy.
- The UI already accepts arbitrary model names; document any custom names for your team.

## Summary

- **Local (student machine)**: run with OpenRouter only – no heavy installs.
- **Remote (resource-rich)**: install Ollama and/or LiteLLM, pull larger models, and start the server with the appropriate environment variables.
- Push to GitHub when ready; the same codebase works in both environments with configuration changes only.

