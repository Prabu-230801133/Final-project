/**
 * VoteX AI Chatbot Widget — chatbot.js
 * Floating chat interface powered by Groq AI
 */

(function () {
  'use strict';

  /* ── Constants ─────────────────────────────────────────────────────── */
  const API_URL   = '/chat/api/';
  const STORAGE_KEY = 'votex_chat_history';
  const MAX_HISTORY = 20; // messages to keep in memory

  const SUGGESTIONS = [
    '🗳️ Active elections?',
    '📊 Current results',
    '❓ How do I vote?',
    '🔐 How to log in?',
    '🏆 Who is winning?',
    '📅 Upcoming elections',
  ];

  const WELCOME_MESSAGE = `👋 Hi! I'm **VoteX Assistant**, your AI guide for this platform.

I can help you with:
• 🗳️ **Election info** — active, upcoming, schedules
• 📊 **Statistics & results** (when published)
• 🧭 **Navigation** — where to go and how to vote
• ❓ **Any questions** about the voting process

What would you like to know?`;

  /* ── State ──────────────────────────────────────────────────────────── */
  let chatHistory = [];   // { role: 'user'|'bot', content: string }
  let isLoading   = false;

  /* ── DOM refs (populated after DOMContentLoaded) ────────────────────── */
  let toggleBtn, chatWindow, messagesEl, inputEl, sendBtn, clearBtn, badgeEl;

  /* ── Initialise ─────────────────────────────────────────────────────── */
  document.addEventListener('DOMContentLoaded', () => {
    injectHTML();
    cacheRefs();
    buildSuggestions();
    loadHistory();
    bindEvents();

    // Show welcome message if first visit
    if (chatHistory.length === 0) {
      appendBotMessage(WELCOME_MESSAGE);
    }
  });

  /* ── HTML injection ─────────────────────────────────────────────────── */
  function injectHTML() {
    const html = `
      <!-- Chat toggle button -->
      <button id="votex-chat-toggle" aria-label="Open VoteX AI Assistant" title="VoteX AI Assistant">
        <span class="chat-icon"><svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg></span>
        <span class="close-icon"><svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg></span>
        <div id="chat-badge">1</div>
      </button>

      <!-- Chat window -->
      <div id="votex-chat-window" role="dialog" aria-label="VoteX AI Assistant Chat">
        <!-- Header -->
        <div id="chat-header">
          <div class="chat-avatar"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg></div>
          <div class="chat-header-info">
            <h4>VoteX Assistant</h4>
            <div class="chat-status">Online · Powered by Groq AI</div>
          </div>
          <button id="chat-clear-btn" title="Clear chat">🗑 Clear</button>
        </div>

        <!-- Quick suggestion pills -->
        <div id="chat-suggestions"></div>

        <!-- Messages -->
        <div id="chat-messages" aria-live="polite" aria-label="Chat messages"></div>

        <!-- Input -->
        <div id="chat-input-area">
          <textarea
            id="chat-input"
            rows="1"
            placeholder="Ask about elections, voting, results…"
            maxlength="1000"
            aria-label="Type your message"
          ></textarea>
          <button id="chat-send-btn" title="Send message" aria-label="Send message">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', html);
  }

  /* ── Cache DOM refs ─────────────────────────────────────────────────── */
  function cacheRefs() {
    toggleBtn  = document.getElementById('votex-chat-toggle');
    chatWindow = document.getElementById('votex-chat-window');
    messagesEl = document.getElementById('chat-messages');
    inputEl    = document.getElementById('chat-input');
    sendBtn    = document.getElementById('chat-send-btn');
    clearBtn   = document.getElementById('chat-clear-btn');
    badgeEl    = document.getElementById('chat-badge');
  }

  /* ── Suggestion pills ───────────────────────────────────────────────── */
  function buildSuggestions() {
    const container = document.getElementById('chat-suggestions');
    SUGGESTIONS.forEach(text => {
      const pill = document.createElement('button');
      pill.className = 'chat-suggestion-pill';
      pill.textContent = text;
      pill.addEventListener('click', () => {
        inputEl.value = text.replace(/^[^\s]+\s/, ''); // strip emoji prefix
        sendMessage();
      });
      container.appendChild(pill);
    });
  }

  /* ── Event bindings ─────────────────────────────────────────────────── */
  function bindEvents() {
    toggleBtn.addEventListener('click', toggleChat);
    sendBtn.addEventListener('click', sendMessage);
    clearBtn.addEventListener('click', clearChat);

    inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    // Auto-resize textarea
    inputEl.addEventListener('input', () => {
      inputEl.style.height = 'auto';
      inputEl.style.height = Math.min(inputEl.scrollHeight, 100) + 'px';
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
      if (
        chatWindow.classList.contains('open') &&
        !chatWindow.contains(e.target) &&
        !toggleBtn.contains(e.target)
      ) {
        // Don't auto-close — keep open for better UX
      }
    });
  }

  /* ── Toggle open/close ──────────────────────────────────────────────── */
  function toggleChat() {
    const isOpen = chatWindow.classList.toggle('open');
    toggleBtn.classList.toggle('open', isOpen);
    if (isOpen) {
      hideBadge();
      requestAnimationFrame(() => inputEl.focus());
      scrollToBottom();
    }
  }

  /* ── Send message ───────────────────────────────────────────────────── */
  function sendMessage() {
    if (isLoading) return;
    const text = inputEl.value.trim();
    if (!text) return;

    appendUserMessage(text);
    inputEl.value = '';
    inputEl.style.height = 'auto';

    const typingEl = showTyping();
    isLoading = true;
    sendBtn.disabled = true;

    // Build history for API (last N messages)
    const historyForApi = chatHistory.slice(-MAX_HISTORY).map(m => ({
      role: m.role === 'user' ? 'user' : 'assistant',
      content: m.content,
    }));

    fetchCsrfToken().then(csrfToken => {
      return fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ message: text, history: historyForApi }),
      });
    })
    .then(res => res.json())
    .then(data => {
      removeTyping(typingEl);
      if (data.reply) {
        appendBotMessage(data.reply);
      } else if (data.error) {
        appendBotMessage(`⚠️ Error: ${data.error}`);
      }
    })
    .catch(err => {
      removeTyping(typingEl);
      appendBotMessage('⚠️ Network error. Please check your connection and try again.');
      console.error('Chat error:', err);
    })
    .finally(() => {
      isLoading = false;
      sendBtn.disabled = false;
      inputEl.focus();
    });
  }

  /* ── Append messages ────────────────────────────────────────────────── */
  function appendUserMessage(text) {
    chatHistory.push({ role: 'user', content: text });
    saveHistory();

    const el = document.createElement('div');
    el.className = 'chat-msg user';
    el.innerHTML = `
      <div class="msg-avatar"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></div>
      <div class="msg-bubble">${escapeHtml(text)}</div>
    `;
    messagesEl.appendChild(el);
    scrollToBottom();
  }

  function appendBotMessage(text) {
    chatHistory.push({ role: 'bot', content: text });
    saveHistory();

    const el = document.createElement('div');
    el.className = 'chat-msg bot';
    el.innerHTML = `
      <div class="msg-avatar"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg></div>
      <div class="msg-bubble">${renderMarkdown(text)}</div>
    `;
    messagesEl.appendChild(el);
    scrollToBottom();

    // Show badge if chat is closed
    if (!chatWindow.classList.contains('open')) {
      showBadge();
    }
  }

  /* ── Typing indicator ───────────────────────────────────────────────── */
  function showTyping() {
    const el = document.createElement('div');
    el.className = 'chat-msg bot';
    el.id = 'chat-typing';
    el.innerHTML = `
      <div class="msg-avatar"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg></div>
      <div class="msg-bubble">
        <div class="typing-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
    `;
    messagesEl.appendChild(el);
    scrollToBottom();
    return el;
  }
  function removeTyping(el) { if (el && el.parentNode) el.parentNode.removeChild(el); }

  /* ── Helpers ────────────────────────────────────────────────────────── */
  function scrollToBottom() {
    requestAnimationFrame(() => {
      messagesEl.scrollTop = messagesEl.scrollHeight;
    });
  }

  function showBadge() {
    if (badgeEl) badgeEl.style.display = 'flex';
  }
  function hideBadge() {
    if (badgeEl) badgeEl.style.display = 'none';
  }

  function clearChat() {
    chatHistory = [];
    saveHistory();
    messagesEl.innerHTML = '';
    appendBotMessage(WELCOME_MESSAGE);
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /** Very lightweight markdown renderer for bot messages */
  function renderMarkdown(text) {
    return text
      // Bold **text**
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // Italic *text*
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      // Bullet points: lines starting with • or -
      .replace(/^[•\-]\s(.+)$/gm, '<li>$1</li>')
      // Wrap consecutive <li> in <ul>
      .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
      // Line breaks
      .replace(/\n/g, '<br>');
  }

  /* ── Persistence (sessionStorage) ──────────────────────────────────── */
  function saveHistory() {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(chatHistory.slice(-MAX_HISTORY)));
    } catch (_) {}
  }
  function loadHistory() {
    try {
      const saved = sessionStorage.getItem(STORAGE_KEY);
      if (saved) {
        chatHistory = JSON.parse(saved);
        chatHistory.forEach(msg => {
          if (msg.role === 'user') appendUserMessageDOM(msg.content);
          else appendBotMessageDOM(msg.content);
        });
        // Reset history to avoid duplicates
        chatHistory = JSON.parse(saved);
      }
    } catch (_) {}
  }
  function appendUserMessageDOM(text) {
    const el = document.createElement('div');
    el.className = 'chat-msg user';
    el.innerHTML = `<div class="msg-avatar"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></div><div class="msg-bubble">${escapeHtml(text)}</div>`;
    messagesEl.appendChild(el);
  }
  function appendBotMessageDOM(text) {
    const el = document.createElement('div');
    el.className = 'chat-msg bot';
    el.innerHTML = `<div class="msg-avatar"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg></div><div class="msg-bubble">${renderMarkdown(text)}</div>`;
    messagesEl.appendChild(el);
  }

  /* ── CSRF token ─────────────────────────────────────────────────────── */
  function fetchCsrfToken() {
    // Try to get it from cookie first (already present in Django pages)
    const cookie = document.cookie.split(';')
      .map(c => c.trim())
      .find(c => c.startsWith('csrftoken='));
    if (cookie) return Promise.resolve(cookie.split('=')[1]);

    // Fallback: fetch from Django's endpoint
    return fetch('/accounts/csrf/', { credentials: 'same-origin' })
      .then(r => r.json())
      .then(d => d.csrfToken)
      .catch(() => '');
  }

})();
