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

  let convo = [];

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
      const url = provider === 'ollama' ? '/api/chat/ollama' : '/api/llm/stream';

      // True streaming; allow cancellation
      const ac = new AbortController();
      currentAbort = ac;
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages, model: provider === 'ollama' ? model : (model || 'qwen-stream') }),
        signal: ac.signal,
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      setStatus('streaming');
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let acc = '';
      let tokens = 0;
      const t0 = performance.now();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        acc += chunk;
        tokens += 1;
        if (onChunk) onChunk(chunk, { tokens, tps: (tokens * 1000) / (performance.now() - t0 + 1) });
      }
      setStatus('idle');
      currentAbort = null;
      return { reply: acc };
    } catch (e) {
      console.error(e);
      setStatus('error');
      currentAbort = null;
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
      addMessage('assistant', 'Sorry, something went wrong.');
    }
  });

  inputEl.addEventListener('input', autoGrowTextarea);
  autoGrowTextarea();

  clearBtn.addEventListener('click', resetChat);
  newChatBtn.addEventListener('click', resetChat);

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
