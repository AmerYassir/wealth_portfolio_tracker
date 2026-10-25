import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Coins, Layers, Loader2 } from 'lucide-react';
import { api } from '../api/client.js';
import AssetTable from '../components/AssetTable.jsx';
import AssetForm from '../components/AssetForm.jsx';
import TransactionTable from '../components/TransactionTable.jsx';
import TransactionForm from '../components/TransactionForm.jsx';
import Members from '../components/Members.jsx';
import ChatPanel from '../components/ChatPanel.jsx';

export default function PortfolioDetail() {
  const { id } = useParams();
  const [portfolio, setPortfolio] = useState(null);
  const [assets, setAssets] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [error, setError] = useState(null);

  function load() {
    Promise.all([api.getPortfolio(id), api.listAssets(id), api.listTransactions(id)])
      .then(([p, a, t]) => { setPortfolio(p); setAssets(a); setTransactions(t); })
      .catch((e) => setError(e.message));
  }
  useEffect(load, [id]);

  if (error) return <div style={{ background: 'var(--danger-soft)', color: 'var(--danger)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)' }}>{error}</div>;
  if (!portfolio) return <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}><Loader2 size={24} style={{ animation: 'spin 1s linear infinite', color: 'var(--text-muted)' }} /></div>;

  const canWrite = portfolio.role === 'OWNER' || portfolio.role === 'EDITOR';
  const isOwner = portfolio.role === 'OWNER';
  const totalCost = assets.reduce((s, a) => s + Number(a.cost_basis), 0);
  const assetById = Object.fromEntries(assets.map((a) => [a.id, a.symbol]));

  async function deleteAsset(a) {
    if (!confirm(`Delete asset ${a.symbol}? This removes its transactions too.`)) return;
    try { await api.deleteAsset(id, a.id); load(); } catch (e) { alert(e.message); }
  }
  async function deleteTransaction(t) {
    if (!confirm('Delete this transaction?')) return;
    try { await api.deleteTransaction(id, t.id); load(); } catch (e) { alert(e.message); }
  }

  return (
    <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
      <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
        <ArrowLeft size={15} /> All portfolios
      </Link>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ marginBottom: '0.25rem' }}>{portfolio.name}</h1>
        <p style={{ color: 'var(--text-muted)', margin: 0 }}>Role: <strong style={{ color: 'var(--accent)' }}>{portfolio.role}</strong></p>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', marginBottom: '2rem' }}>
        <StatCard icon={<Layers size={16} />} label="Assets" value={assets.length} />
        <StatCard icon={<Coins size={16} />} label="Total cost basis" value={`$${totalCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`} />
        <StatCard icon={<Layers size={16} />} label="Transactions" value={transactions.length} />
      </div>

      <Section title="Assets">
        {canWrite && <AssetForm portfolioId={id} onCreated={load} />}
        <AssetTable assets={assets} canWrite={canWrite} onDelete={deleteAsset} />
      </Section>
      <Section title="Transactions">
        {canWrite && <TransactionForm portfolioId={id} assets={assets} onCreated={load} />}
        <TransactionTable transactions={transactions} assetById={assetById} canWrite={canWrite} onDelete={deleteTransaction} />
      </Section>
      <Members portfolioId={id} isOwner={isOwner} />
      <ChatPanel portfolioId={portfolio.id} portfolioName={portfolio.name} />
    </div>
  );
}

function Section({ title, children }) { return <section style={{ marginBottom: '2rem' }}><h2 style={{ marginBottom: '0.75rem' }}>{title}</h2>{children}</section>; }
function StatCard({ icon, label, value }) { return <div style={{ background: 'var(--bg-elev)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '1rem' }}><div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '0.4rem' }}>{icon}{label}</div><div className="num" style={{ fontSize: '1.4rem', fontWeight: 600 }}>{value}</div></div>; }
