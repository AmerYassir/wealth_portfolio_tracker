import { useEffect, useRef, useState } from 'react';
import { Bot, Send, Sparkles, RotateCcw, AlertCircle } from 'lucide-react';
import { getToken } from '../auth.js';

function uuid() {
  return crypto.randomUUID ? crypto.randomUUID() : String(Math.random()).slice(2);
}

const SUGGESTIONS = [
  "What's my asset breakdown?",
  'Show transactions from 2024',
  'What is my role on this portfolio?',
];

export default function ChatPanel({ portfolioId, portfolioName }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [toolActive, setToolActive] = useState(false);
  const [error, setError] = useState(null);
  const scrollerRef = useRef(null);
  const pinnedRef = useRef(true);

  useEffect(() => {
    const el = scrollerRef.current;
    if (el && pinnedRef.current) el.scrollTop = el.scrollHeight;
  }, [messages, toolActive]);

  function onScroll() {
    const el = scrollerRef.current;
    if (!el) return;
    pinnedRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
  }

  async function send(text) {
    const content = (text ?? input).trim();
    if (!content || streaming) return;
    const userMsg = { id: uuid(), role: 'user', content };
    const assistantId = uuid();
    const history = [...messages, userMsg];
    setMessages([...history, { id: assistantId, role: 'assistant', content: '', streaming: true }]);
    setInput('');
    setStreaming(true); setToolActive(false); setError(null);

    const body = {
      threadId: `ui-${portfolioId}`, runId: uuid(),
      messages: history.map((m) => ({ id: m.id, role: m.role, content: m.content })),
      tools: [], context: [], state: null, forwardedProps: {},
    };

    try {
      const resp = await fetch('/agent/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify(body),
      });
      if (!resp.ok || !resp.body) throw new Error(`HTTP ${resp.status}`);

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buf = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        let idx;
        while ((idx = buf.indexOf('\n\n')) !== -1) {
          const block = buf.slice(0, idx); buf = buf.slice(idx + 2);
          handleBlock(block, assistantId);
        }
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setStreaming(false); setToolActive(false);
      setMessages((m) => m.map((x) => x.id === assistantId ? { ...x, streaming: false } : x));
    }
  }

  function handleBlock(block, assistantId) {
    for (const line of block.split('\n')) {
      if (!line.startsWith('data:')) continue;
      const payload = line.slice(5).trim();
      if (!payload) continue;
      let ev; try { ev = JSON.parse(payload); } catch { continue; }

      if (ev.type === 'TEXT_MESSAGE_CONTENT') {
        const delta = ev.delta || '';
        setMessages((m) => m.map((x) => x.id === assistantId ? { ...x, content: x.content + delta } : x));
      } else if (ev.type === 'TOOL_CALL_START') {
        setToolActive(true);
      } else if (ev.type === 'TOOL_CALL_END') {
        setToolActive(false);
      } else if (ev.type === 'RUN_ERROR') {
        setMessages((m) => m.map((x) => x.id === assistantId
          ? { ...x, content: x.content + `\n[agent error: ${ev.message || 'unknown'}]`, streaming: false }
          : x));
      }
    }
  }

  function reset() { setMessages([]); setError(null); }

  return (
    <section style={{
      marginTop: '2.5rem', background: 'var(--bg-elev)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius)', overflow: 'hidden', boxShadow: 'var(--shadow-sm)',
    }}>
      <header style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0.9rem 1.1rem', borderBottom: '1px solid var(--border)', background: 'var(--bg-elev-2)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{ width: 30, height: 30, borderRadius: 8, background: 'var(--accent-soft)', color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Sparkles size={16} />
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>Ask about {portfolioName}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Read-only agent, scoped to your access</div>
          </div>
        </div>
        {messages.length > 0 && (
          <button onClick={reset} style={{ padding: '0.4rem 0.6rem', display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8rem' }} title="New chat">
            <RotateCcw size={13} /> New
          </button>
        )}
      </header>

      <div ref={scrollerRef} onScroll={onScroll} style={{ maxHeight: 380, minHeight: 160, overflowY: 'auto', padding: '1rem' }}>
        {messages.length === 0 && !error && (
          <div style={{ textAlign: 'center', padding: '1rem 0' }}>
            <Bot size={36} style={{ color: 'var(--text-faint)', marginBottom: '0.5rem' }} />
            <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>Ask a question about this portfolio.</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', justifyContent: 'center' }}>
              {SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => send(s)} style={{ fontSize: '0.82rem', padding: '0.4rem 0.75rem', borderRadius: 999, background: 'var(--bg-elev-2)' }}>{s}</button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        {toolActive && <ToolPill />}
        {error && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--danger-soft)', color: 'var(--danger)', padding: '0.65rem 0.85rem', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem', marginTop: '0.5rem' }}>
            <AlertCircle size={14} /> {error}
          </div>
        )}
      </div>

      <div style={{ padding: '0.85rem', borderTop: '1px solid var(--border)', background: 'var(--bg-elev-2)', display: 'flex', gap: '0.5rem' }}>
        <input
          value={input} onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
          placeholder="Ask the agent…" disabled={streaming}
          style={{ flex: 1, background: 'var(--bg-elev)' }}
        />
        <button className="primary" onClick={() => send()} disabled={streaming || !input.trim()}
                style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.55rem 1rem' }}>
          {streaming ? <span style={{ width: 14, height: 14, border: '2px solid #fff', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} /> : <Send size={14} />}
          Send
        </button>
      </div>
    </section>
  );
}

function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  return (
    <div style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', marginBottom: '0.75rem', animation: 'fadeIn 0.25s ease-out' }}>
      <div style={{
        maxWidth: '80%', padding: '0.6rem 0.85rem',
        borderRadius: 'var(--radius)',
        borderTopRightRadius: isUser ? 4 : 'var(--radius)',
        borderTopLeftRadius: isUser ? 'var(--radius)' : 4,
        background: isUser ? 'var(--accent)' : 'var(--bg-elev-2)',
        color: isUser ? '#fff' : 'var(--text)',
        fontSize: '0.9rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
      }}>
        {message.content || (message.streaming ? <TypingDots /> : '')}
      </div>
    </div>
  );
}

function TypingDots() {
  return (
    <span style={{ display: 'inline-flex', gap: '0.2rem', alignItems: 'center', padding: '0.2rem 0' }}>
      {[0, 1, 2].map((i) => (
        <span key={i} style={{
          width: 6, height: 6, borderRadius: '50%', background: 'var(--text-muted)',
          animation: `bounceDot 1.2s infinite ${i * 0.15}s`,
        }} />
      ))}
    </span>
  );
}

function ToolPill() {
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.35rem 0.75rem', borderRadius: 999, background: 'var(--accent-soft)', color: 'var(--accent)', fontSize: '0.8rem', marginBottom: '0.5rem', animation: 'fadeIn 0.2s ease-out' }}>
      <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent)', animation: 'pulse 1.2s infinite' }} />
      Calling tool…
    </div>
  );
}
