import { useState } from 'react';
import { api } from '../api/client.js';

export default function TransactionForm({ portfolioId, assets, onCreated }) {
  const [form, setForm] = useState({ asset: assets[0]?.id || '', type: 'BUY', amount: '', occurred_at: new Date().toISOString().slice(0, 10) });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })); }

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setError(null);
    try {
      const payload = { ...form, asset: Number(form.asset), occurred_at: new Date(form.occurred_at).toISOString() };
      await api.createTransaction(portfolioId, payload);
      setForm((f) => ({ ...f, amount: '' }));
      onCreated();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  if (!assets.length) return <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Add an asset first, then you can log transactions.</p>;

  return (
    <form onSubmit={submit} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.5rem', alignItems: 'end', background: 'var(--bg-elev)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '1rem', marginBottom: '0.75rem' }}>
      <Field label="Asset">
        <select value={form.asset} onChange={(e) => set('asset', e.target.value)} style={selectStyle}>
          {assets.map((a) => <option key={a.id} value={a.id}>{a.symbol}</option>)}
        </select>
      </Field>
      <Field label="Type">
        <select value={form.type} onChange={(e) => set('type', e.target.value)} style={selectStyle}>
          <option value="BUY">Buy</option><option value="SELL">Sell</option><option value="DIVIDEND">Dividend</option>
        </select>
      </Field>
      <Field label="Amount ($)"><input type="number" step="any" value={form.amount} onChange={(e) => set('amount', e.target.value)} placeholder="1000" /></Field>
      <Field label="Date"><input type="date" value={form.occurred_at} onChange={(e) => set('occurred_at', e.target.value)} /></Field>
      <button type="submit" className="primary" disabled={busy || !form.amount || !form.asset}>{busy ? 'Adding…' : 'Add transaction'}</button>
      {error && <p style={{ gridColumn: '1 / -1', color: 'var(--danger)', fontSize: '0.85rem', margin: 0 }}>{error}</p>}
    </form>
  );
}

const selectStyle = { width: '100%', padding: '0.55rem 0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', background: 'var(--bg-elev)', color: 'var(--text)', fontFamily: 'inherit', fontSize: '0.95rem' };
function Field({ label, children }) { return <label style={{ display: 'block' }}><span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>{label}</span>{children}</label>; }
