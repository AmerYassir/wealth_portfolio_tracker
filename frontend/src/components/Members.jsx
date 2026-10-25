import { useEffect, useState } from 'react';
import { UserPlus, Users, X } from 'lucide-react';
import { api } from '../api/client.js';

const ROLE_COLORS = { OWNER: 'var(--accent)', EDITOR: '#3b82f6', VIEWER: 'var(--text-muted)' };

export default function Members({ portfolioId, isOwner }) {
  const [members, setMembers] = useState(null);
  const [error, setError] = useState(null);

  function load() {
    api.listMembers(portfolioId).then(setMembers).catch((e) => setError(e.message));
  }
  useEffect(load, [portfolioId]);

  async function remove(m) {
    if (!confirm(`Remove ${m.username} from this portfolio?`)) return;
    try { await api.removeMember(portfolioId, m.id); load(); }
    catch (e) { alert(e.message); }
  }

  return (
    <section style={{ marginBottom: '2rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
        <Users size={18} />
        <h2>Members</h2>
      </div>

      {error && <div style={{ background: 'var(--danger-soft)', color: 'var(--danger)', padding: '0.6rem 0.85rem', borderRadius: 'var(--radius-sm)', marginBottom: '0.5rem' }}>{error}</div>}

      {members === null ? (
        <p style={{ color: 'var(--text-muted)' }}>Loading…</p>
      ) : (
        <div style={{ background: 'var(--bg-elev)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'var(--bg-elev-2)', borderBottom: '1px solid var(--border)' }}>
                <Th>User</Th><Th>Role</Th>{isOwner && <Th align="right" />}
              </tr>
            </thead>
            <tbody>
              {members.map((m) => (
                <tr key={m.id} style={{ borderBottom: '1px solid var(--border)' }}>
                  <Td><strong>{m.username}</strong></Td>
                  <Td><span style={{ fontSize: '0.8rem', fontWeight: 600, color: ROLE_COLORS[m.role] || 'var(--text-muted)', letterSpacing: '0.03em' }}>{m.role}</span></Td>
                  {isOwner && (
                    <Td align="right">
                      {m.role !== 'OWNER' && (
                        <button onClick={() => remove(m)} style={{ padding: '0.25rem', color: 'var(--text-muted)' }} title="Remove"><X size={14} /></button>
                      )}
                    </Td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {isOwner && <InviteForm portfolioId={portfolioId} onInvited={load} />}
    </section>
  );
}

function InviteForm({ portfolioId, onInvited }) {
  const [username, setUsername] = useState('');
  const [role, setRole] = useState('VIEWER');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setError(null);
    try { await api.inviteMember(portfolioId, username.trim(), role); setUsername(''); onInvited(); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  return (
    <form onSubmit={submit} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr auto', gap: '0.5rem', alignItems: 'end', marginTop: '0.75rem', background: 'var(--bg-elev)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '1rem' }}>
      <label>
        <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Username</span>
        <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="e.g. alice" />
      </label>
      <label>
        <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Role</span>
        <select value={role} onChange={(e) => setRole(e.target.value)} style={{ width: '100%', padding: '0.55rem 0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', background: 'var(--bg-elev)', color: 'var(--text)', fontFamily: 'inherit', fontSize: '0.95rem' }}>
          <option value="VIEWER">Viewer</option>
          <option value="EDITOR">Editor</option>
        </select>
      </label>
      <button type="submit" className="primary" disabled={busy || !username.trim()} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
        <UserPlus size={15} /> {busy ? 'Inviting…' : 'Invite'}
      </button>
      {error && <p style={{ gridColumn: '1 / -1', color: 'var(--danger)', fontSize: '0.85rem', margin: 0 }}>{error}</p>}
    </form>
  );
}

function Th({ children, align = 'left' }) { return <th style={{ textAlign: align, padding: '0.7rem 1rem', fontSize: '0.75rem', fontWeight: 500, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{children}</th>; }
function Td({ children, align = 'left' }) { return <td style={{ textAlign: align, padding: '0.75rem 1rem', fontSize: '0.9rem' }}>{children}</td>; }
