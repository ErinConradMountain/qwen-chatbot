(() => {
  const el = (sel, root = document) => root.querySelector(sel);
  const messagesEl = el('#messages');
  const inputEl = el('#input');
  const formEl = el('#composer');
  const fileInputEl = el('#file-input');
  const attachBtn = el('#attach');
  const attachmentsEl = el('#attachments');
  const clearBtn = el('#clear-chat');
  const newChatBtn = el('#new-chat');
  const statusDot = el('#status-dot');
  const statusText = el('#status-text');
  const toggleTheme = el('#toggle-theme');
  const sysPromptEl = el('#system-prompt');
  const modelNameEl = el('#model-name');
  const banner = el('#banner');
  const bannerText = el('#banner-text');
  const bannerDismiss = el('#banner-dismiss');
  const testConnBtn = el('#test-conn');

  let convo = [];
  let pendingImages = [];

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
    // Render string or multimodal array
    if (Array.isArray(content)) {
      content.forEach(part => {
        if (part.type === 'text') {
          const p = document.createElement('p');
          p.textContent = part.text || '';
          bubble.appendChild(p);
        } else if (part.type === 'image_url' && part.image_url && part.image_url.url) {
          const img = document.createElement('img');
          img.src = part.image_url.url;
          img.alt = part.image_url.alt || 'attached image';
          img.style.maxWidth = '240px';
          img.style.borderRadius = '8px';
          img.style.display = 'block';
          img.style.margin = '6px 0';
          bubble.appendChild(img);
        }
      });
    } else {
      const p = document.createElement('p');
      p.textContent = content;
      bubble.appendChild(p);
    }
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
          model: (modelNameEl?.value || '').trim() || undefined,
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
    if (!text && pendingImages.length === 0) return;

    // Build multimodal content for user
    let userContent;
    if (pendingImages.length > 0) {
      userContent = [];
      if (text) userContent.push({ type: 'text', text });
      pendingImages.forEach(url => {
        userContent.push({ type: 'image_url', image_url: { url } });
      });
    } else {
      userContent = text;
    }

    addMessage('user', userContent);
    inputEl.value = '';
    autoGrowTextarea();
    pendingImages = [];
    attachmentsEl.innerHTML = '';

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

  // Image attachment workflow
  function addAttachmentPreview(url) {
    const wrap = document.createElement('div');
    wrap.className = 'attachment';
    const img = document.createElement('img');
    img.src = url;
    img.alt = 'attachment preview';
    img.style.maxWidth = '96px';
    img.style.maxHeight = '96px';
    img.style.objectFit = 'cover';
    img.style.borderRadius = '6px';
    img.style.marginRight = '6px';
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'icon-btn';
    removeBtn.textContent = '×';
    removeBtn.title = 'Remove';
    removeBtn.addEventListener('click', () => {
      const idx = pendingImages.indexOf(url);
      if (idx >= 0) pendingImages.splice(idx, 1);
      attachmentsEl.removeChild(wrap);
    });
    wrap.appendChild(img);
    wrap.appendChild(removeBtn);
    attachmentsEl.appendChild(wrap);
  }

  attachBtn.addEventListener('click', () => fileInputEl.click());

  fileInputEl.addEventListener('change', async (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    for (const f of files) {
      if (!f.type.startsWith('image/')) continue;
      const dataUrl = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(f);
      });
      pendingImages.push(String(dataUrl));
      addAttachmentPreview(String(dataUrl));
    }
    // reset input to allow re-selection of same files
    fileInputEl.value = '';
  });

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
      const savedMessages = JSON.parse(saved);
      convo = [];
      savedMessages.forEach((m) => addMessage(m.role, m.content));
    }
  } catch {
    /* ignore restore issues */
  }
})();
