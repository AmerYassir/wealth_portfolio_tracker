import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Loader2, UserPlus } from 'lucide-react';
import { register } from '../api/client.js';
import { setTokens } from '../auth.js';

export default function Signup() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();

  async function onSubmit(e) {
    e.preventDefault();
    setError(null); setBusy(true);
    try {
      const tokens = await register(username, password, email);
      setTokens(tokens.access, tokens.refresh);
      nav('/');
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  return (
    <div style={{ maxWidth: 380, margin: '4rem auto', animation: 'fadeIn 0.3s ease-out' }}>
      <div style={{ background: 'var(--bg-elev)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '2rem', boxShadow: 'var(--shadow-md)' }}>
        <h1 style={{ marginBottom: '0.25rem' }}>Create account</h1>
        <p style={{ color: 'var(--text-muted)', marginTop: 0, marginBottom: '1.5rem', fontSize: '0.9rem' }}>Start your own portfolio</p>
        <form onSubmit={onSubmit}>
          <label style={{ display: 'block', marginBottom: '0.9rem' }}>
            <span style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>Username</span>
            <input value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
          </label>
          <label style={{ display: 'block', marginBottom: '0.9rem' }}>
            <span style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>Email <span style={{ color: 'var(--text-faint)' }}>(optional)</span></span>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          <label style={{ display: 'block', marginBottom: '1rem' }}>
            <span style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>Password <span style={{ color: 'var(--text-faint)' }}>(min 8 chars)</span></span>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {error && <div style={{ background: 'var(--danger-soft)', color: 'var(--danger)', padding: '0.6rem 0.75rem', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem', marginBottom: '1rem' }}>{error}</div>}
          <button type="submit" className="primary" disabled={busy || !username || password.length < 8} style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', padding: '0.65rem' }}>
            {busy ? <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> : <UserPlus size={16} />}
            {busy ? 'Creating…' : 'Create account'}
          </button>
        </form>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textAlign: 'center', marginTop: '1.25rem', marginBottom: 0 }}>
          Already have one? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
