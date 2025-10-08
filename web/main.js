(() => {
  const el = (sel, root = document) => root.querySelector(sel);
  const messagesEl = el('#messages');
  const inputEl = el('#input');
  const formEl = el('#composer');
  const clearBtn = el('#clear-chat');
  const newChatBtn = el('#new-chat');
  const statusDot = el('#status-dot');
  const statusText = el('#status-text');
  const toggleTheme = el('#toggle-theme');
  const providerEl = el('#provider');
  const modelEl = el('#model');
  const sysPromptEl = el('#system-prompt');
  const banner = el('#banner');
  const bannerText = el('#banner-text');
  const bannerSwitch = el('#banner-switch');
  const bannerDismiss = el('#banner-dismiss');
  const testConnBtn = el('#test-conn');

  let convo = [];
  // Default provider to Ollama for reliable local runs
  if (providerEl && !localStorage.getItem('provider_pref')) {
    providerEl.value = 'ollama';
  } else {
    const pv = localStorage.getItem('provider_pref');
    if (pv) providerEl.value = pv;
  }
  providerEl?.addEventListener('change', () => localStorage.setItem('provider_pref', providerEl.value));

  function setStatus(state) {
    const map = { idle: ['#94a3b8', 'Idle'], sending: ['#f59e0b', 'Sending...'], streaming: ['#22c55e', 'Streaming...'], error: ['#ef4444', 'Error'] };
    const [color, text] = map[state] || map.idle;
    statusDot.style.background = color;
    statusText.textContent = text;
  }

  function autoGrowTextarea() {
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(160, Math.max(44, inputEl.scrollHeight)) + 'px';
  }

  function addMessage(role, content) {
    convo.push({ role, content });
    const item = document.createElement('div');
    item.className = 'message';
    const avatar = document.createElement('div');
    avatar.className = `avatar ${role === 'user' ? 'user' : 'bot'}`;
    avatar.textContent = role === 'user' ? 'U' : 'A';
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    const p = document.createElement('p');
    p.textContent = content;
    bubble.appendChild(p);
    item.appendChild(avatar);
    item.appendChild(bubble);
    messagesEl.appendChild(item);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function resetChat() {
    convo = [];
    messagesEl.innerHTML = '';
    localStorage.removeItem('qwen_chat');
    setStatus('idle');
  }

  let currentAbort = null;

  async function send(messages, onChunk) {
    setStatus('sending');
    try {
      const provider = providerEl.value || 'qwen';
      const model = (modelEl.value || '').trim() || undefined;
      const url = provider === 'ollama'
        ? '/api/chat/ollama'
        : (provider === 'qwen' ? '/api/chat/qwen' : '/api/llm/stream');

      // True streaming; allow cancellation
      const ac = new AbortController();
      currentAbort = ac;
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages,
          model: provider === 'ollama' ? model : (provider === 'qwen' ? model : (model || 'qwen-stream')),
          system_prompt: (sysPromptEl?.value || '').trim() || undefined,
        }),
        signal: ac.signal,
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      setStatus('streaming');
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let acc = '';
      let buffer = '';
      let tokens = 0;
      const t0 = performance.now();
      let lastFlush = 0;
      const flush = () => {
        if (!buffer) return;
        const out = buffer;
        buffer = '';
        tokens += 1;
        if (onChunk) onChunk(out, { tokens, tps: (tokens * 1000) / (performance.now() - t0 + 1) });
      };
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        acc += chunk;
        buffer += chunk;
        const now = performance.now();
        const shouldFlush = buffer.endsWith('\n') || /[\.!?，。！？]$/.test(buffer) || (now - lastFlush) > 40;
        if (shouldFlush) { flush(); lastFlush = now; }
      }
      flush();
      setStatus('idle');
      currentAbort = null;
      return { reply: acc };
    } catch (e) {
      console.error(e);
      setStatus('error');
      currentAbort = null;
      // If proxy path failed, suggest switching to Ollama
      try {
        const provider = providerEl.value || 'qwen';
        if (provider !== 'ollama') {
          banner.hidden = false;
          bannerText.textContent = 'Proxy not reachable (or error). Switch to Ollama local?';
        }
      } catch {}
      throw e;
    }
  }

  formEl.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = (inputEl.value || '').trim();
    if (!text) return;
    addMessage('user', text);
    inputEl.value = '';
    autoGrowTextarea();
    try {
      // Create placeholder message to stream into
      const placeholder = { role: 'assistant', content: '' };
      convo.push(placeholder);
      const item = document.createElement('div');
      item.className = 'message';
      const avatar = document.createElement('div');
      avatar.className = 'avatar bot';
      avatar.textContent = 'A';
      const bubble = document.createElement('div');
      bubble.className = 'bubble';
      const p = document.createElement('p');
      p.textContent = '';
      bubble.appendChild(p);
      item.appendChild(avatar);
      item.appendChild(bubble);
      messagesEl.appendChild(item);
      messagesEl.scrollTop = messagesEl.scrollHeight;

      // Add a cancel button and stats area
      const meta = document.createElement('div');
      meta.style.fontSize = '12px';
      meta.style.color = 'var(--muted)';
      meta.style.marginTop = '6px';
      const stopBtn = document.createElement('button');
      stopBtn.className = 'icon-btn';
      stopBtn.textContent = '⏹️ Stop';
      stopBtn.style.marginLeft = '8px';
      stopBtn.onclick = () => { if (currentAbort) currentAbort.abort(); };
      bubble.appendChild(meta);
      bubble.appendChild(stopBtn);

      const out = await send(convo, (chunk, stats) => {
        p.textContent += chunk;
        meta.textContent = `${stats.tokens} tokens • ${stats.tps.toFixed(1)} tok/s`;
        messagesEl.scrollTop = messagesEl.scrollHeight;
      });
      const reply = out && out.reply ? out.reply : '(no reply)';
      p.textContent = reply;
      placeholder.content = reply;
      localStorage.setItem('qwen_chat', JSON.stringify(convo));
    } catch (e) {
      addMessage('assistant', `[error] ${e && e.message ? e.message : 'request failed'}`);
    }
  });

  inputEl.addEventListener('input', autoGrowTextarea);
  autoGrowTextarea();

  clearBtn.addEventListener('click', resetChat);
  newChatBtn.addEventListener('click', resetChat);
  bannerSwitch.addEventListener('click', () => { providerEl.value = 'ollama'; banner.hidden = true; });
  bannerDismiss.addEventListener('click', () => { banner.hidden = true; });
  testConnBtn.addEventListener('click', async () => {
    setStatus('sending');
    try {
      const res = await fetch('/api/health', { method: 'GET' });
      const data = await res.json();
      const litellmOk = data.detail && data.detail.litellm === 200;
      const ollamaOk = data.detail && data.detail.ollama === 200;
      banner.hidden = false;
      if (litellmOk && ollamaOk) {
        bannerText.textContent = 'Connections OK: LiteLLM and Ollama are reachable.';
        statusDot.classList.remove('warn','err');
        statusDot.classList.add('ok');
      } else if (ollamaOk) {
        bannerText.textContent = 'Ollama is reachable. LiteLLM proxy not reachable.';
        statusDot.classList.remove('ok','err');
        statusDot.classList.add('warn');
      } else {
        bannerText.textContent = 'No backends reachable. Start Ollama or the proxy.';
        statusDot.classList.remove('ok','warn');
        statusDot.classList.add('err');
      }
      setStatus('idle');
    } catch (e) {
      banner.hidden = false;
      bannerText.textContent = 'Health check failed. Is the server running?';
      statusDot.classList.remove('ok','warn');
      statusDot.classList.add('err');
      setStatus('error');
    }
  });

  toggleTheme.addEventListener('click', () => {
    const v = document.documentElement.getAttribute('data-theme');
    const next = v === 'light' ? 'dark' : v === 'dark' ? null : 'light';
    if (next) document.documentElement.setAttribute('data-theme', next);
    else document.documentElement.removeAttribute('data-theme');
  });

  // Restore last chat
  try {
    const saved = localStorage.getItem('qwen_chat');
    if (saved) {
      convo = JSON.parse(saved);
      convo.forEach(m => addMessage(m.role, m.content));
    }
  } catch {}
})();
