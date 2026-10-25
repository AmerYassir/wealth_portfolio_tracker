import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, LogIn } from 'lucide-react';
import { login } from '../api/client.js';
import { setTokens } from '../auth.js';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();

  async function onSubmit(e) {
    e.preventDefault();
    setError(null); setBusy(true);
    try {
      const tokens = await login(username, password);
      setTokens(tokens.access, tokens.refresh);
      nav('/');
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  return (
    <div style={{ maxWidth: 380, margin: '4rem auto', animation: 'fadeIn 0.3s ease-out' }}>
      <div style={{
        background: 'var(--bg-elev)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius)', padding: '2rem', boxShadow: 'var(--shadow-md)',
      }}>
        <h1 style={{ marginBottom: '0.25rem' }}>Sign in</h1>
        <p style={{ color: 'var(--text-muted)', marginTop: 0, marginBottom: '1.5rem', fontSize: '0.9rem' }}>
          Wealth Portfolio Tracker
        </p>
        <form onSubmit={onSubmit}>
          <label style={{ display: 'block', marginBottom: '0.9rem' }}>
            <span style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>Username</span>
            <input value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
          </label>
          <label style={{ display: 'block', marginBottom: '1rem' }}>
            <span style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>Password</span>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {error && (
            <div style={{ background: 'var(--danger-soft)', color: 'var(--danger)', padding: '0.6rem 0.75rem', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem', marginBottom: '1rem' }}>
              {error}
            </div>
          )}
          <button type="submit" className="primary" disabled={busy || !username || !password}
                  style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', padding: '0.65rem' }}>
            {busy ? <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> : <LogIn size={16} />}
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-faint)', textAlign: 'center', marginTop: '1.25rem', marginBottom: 0 }}>
          Try <code style={{ background: 'var(--bg-elev-2)', padding: '0.1rem 0.35rem', borderRadius: 4 }}>viewer</code> / <code style={{ background: 'var(--bg-elev-2)', padding: '0.1rem 0.35rem', borderRadius: 4 }}>pass1234</code>
        </p>
      </div>
    </div>
  );
}
