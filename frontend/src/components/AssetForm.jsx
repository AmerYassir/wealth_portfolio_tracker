import { useState } from 'react';
import { api } from '../api/client.js';

export default function AssetForm({ portfolioId, onCreated }) {
  const [form, setForm] = useState({ type: 'STOCK', symbol: '', quantity: '', cost_basis: '' });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })); }

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setError(null);
    try {
      await api.createAsset(portfolioId, form);
      setForm({ type: 'STOCK', symbol: '', quantity: '', cost_basis: '' });
      onCreated();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  return (
    <form onSubmit={submit} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.5rem', alignItems: 'end', background: 'var(--bg-elev)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '1rem', marginBottom: '0.75rem' }}>
      <Field label="Type">
        <select value={form.type} onChange={(e) => set('type', e.target.value)} style={{ width: '100%', padding: '0.55rem 0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', background: 'var(--bg-elev)', color: 'var(--text)', fontFamily: 'inherit', fontSize: '0.95rem' }}>
          <option value="STOCK">Stock</option><option value="CRYPTO">Crypto</option><option value="REAL_ESTATE">Real estate</option><option value="CASH">Cash</option>
        </select>
      </Field>
      <Field label="Symbol"><input value={form.symbol} onChange={(e) => set('symbol', e.target.value.toUpperCase())} placeholder="AAPL" /></Field>
      <Field label="Quantity"><input type="number" step="any" value={form.quantity} onChange={(e) => set('quantity', e.target.value)} placeholder="10" /></Field>
      <Field label="Cost basis ($)"><input type="number" step="any" value={form.cost_basis} onChange={(e) => set('cost_basis', e.target.value)} placeholder="1000" /></Field>
      <button type="submit" className="primary" disabled={busy || !form.symbol || !form.quantity || !form.cost_basis}>{busy ? 'Adding…' : 'Add asset'}</button>
      {error && <p style={{ gridColumn: '1 / -1', color: 'var(--danger)', fontSize: '0.85rem', margin: 0 }}>{error}</p>}
    </form>
  );
}

function Field({ label, children }) { return <label style={{ display: 'block' }}><span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>{label}</span>{children}</label>; }
