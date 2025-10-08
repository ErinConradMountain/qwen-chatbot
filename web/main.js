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
  const sysPromptEl = el('#system-prompt');
  const banner = el('#banner');
  const bannerText = el('#banner-text');
  const bannerDismiss = el('#banner-dismiss');
  const testConnBtn = el('#test-conn');

  let convo = [];

  const STATUS_MAP = {
    idle: ['#94a3b8', 'Idle'],
    sending: ['#f59e0b', 'Sending...'],
    error: ['#ef4444', 'Error'],
  };

  const QWEN_ENDPOINT = '/api/chat/qwen';

  function setStatus(state) {
    const [color, text] = STATUS_MAP[state] || STATUS_MAP.idle;
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
    banner.hidden = true;
    setStatus('idle');
  }

  async function send(messages) {
    setStatus('sending');
    try {
      const res = await fetch(QWEN_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages,
          system_prompt: (sysPromptEl?.value || '').trim() || undefined,
        }),
      });

      const contentType = res.headers.get('content-type') || '';
      const isJson = contentType.includes('application/json');

      if (!res.ok) {
        let detail = `HTTP ${res.status}`;
        if (isJson) {
          try {
            const payload = await res.json();
            if (payload && payload.detail) detail = payload.detail;
          } catch {
            /* ignore parse errors */
          }
        }
        throw new Error(detail);
      }

      const data = isJson ? await res.json() : { reply: await res.text() };
      const reply = data && typeof data.reply === 'string' ? data.reply : '';
      setStatus('idle');
      banner.hidden = true;
      return { reply };
    } catch (e) {
      console.error(e);
      setStatus('error');
      banner.hidden = false;
      bannerText.textContent = 'Request failed. Check API key/server and try again.';
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

    try {
      const outbound = convo.slice(0, -1);
      const out = await send(outbound);
      const reply = out && out.reply ? out.reply : '(no reply)';
      p.textContent = reply;
      placeholder.content = reply;
      localStorage.setItem('qwen_chat', JSON.stringify(convo));
    } catch (err) {
      const message = err && err.message ? err.message : 'request failed';
      p.textContent = `[error] ${message}`;
      placeholder.content = p.textContent;
    }
  });

  inputEl.addEventListener('input', autoGrowTextarea);
  autoGrowTextarea();

  clearBtn.addEventListener('click', resetChat);
  newChatBtn.addEventListener('click', resetChat);
  bannerDismiss.addEventListener('click', () => { banner.hidden = true; });

  testConnBtn.addEventListener('click', async () => {
    setStatus('sending');
    try {
      const res = await fetch('/api/health', { method: 'GET' });
      const data = await res.json();
      banner.hidden = false;
      if (data.ok) {
        bannerText.textContent = 'Health OK: API key detected. You can chat.';
        statusDot.classList.remove('warn', 'err');
        statusDot.classList.add('ok');
        setStatus('idle');
      } else {
        bannerText.textContent = 'Health failed: missing API key. Set OPENROUTER_API_KEY in .env and restart.';
        statusDot.classList.remove('ok', 'warn');
        statusDot.classList.add('err');
        setStatus('error');
      }
    } catch (e) {
      console.error(e);
      banner.hidden = false;
      bannerText.textContent = 'Health check failed. Is the server running?';
      statusDot.classList.remove('ok', 'warn');
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

  try {
    const saved = localStorage.getItem('qwen_chat');
    if (saved) {
      convo = JSON.parse(saved);
      convo.forEach((m) => addMessage(m.role, m.content));
    }
  } catch {
    /* ignore restore issues */
  }
})();
