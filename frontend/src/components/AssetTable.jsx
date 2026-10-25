import { Package, Trash2 } from 'lucide-react';

export default function AssetTable({ assets, canWrite, onDelete }) {
  if (!assets.length) return <p style={{ color: 'var(--text-muted)', padding: '1.5rem 0' }}>No assets yet.</p>;
  return (
    <div style={{ background: 'var(--bg-elev)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ background: 'var(--bg-elev-2)', borderBottom: '1px solid var(--border)' }}>
            {/* <Th>Symbol</Th><Th>Type</Th><Th align="right">Quantity</Th><Th align="right">Cost basis</Th> */}
            <Th>ID</Th><Th>Symbol</Th><Th>Type</Th><Th align="right">Quantity</Th><Th align="right">Cost basis</Th>
            {canWrite && <Th align="right" />}
          </tr>
        </thead>
        <tbody>
          {assets.map((a) => (
            <tr key={a.id} style={{ borderBottom: '1px solid var(--border)' }}>
                <Td>{a.id}</Td>
              <Td><span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}><Package size={14} style={{ color: 'var(--text-muted)' }} />{a.symbol}</span></Td>
              <Td><TypePill type={a.type} /></Td>
              <Td align="right" className="num">{a.quantity}</Td>
              <Td align="right" className="num">${Number(a.cost_basis).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</Td>
              {canWrite && <Td align="right"><button onClick={() => onDelete(a)} style={{ padding: '0.25rem', color: 'var(--text-muted)' }} title="Delete"><Trash2 size={14} /></button></Td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
function Th({ children, align = 'left' }) { return <th style={{ textAlign: align, padding: '0.7rem 1rem', fontSize: '0.75rem', fontWeight: 500, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{children}</th>; }
function Td({ children, align = 'left', className = '' }) { return <td className={className} style={{ textAlign: align, padding: '0.75rem 1rem', fontSize: '0.9rem' }}>{children}</td>; }
function TypePill({ type }) {
  const colors = { STOCK: '#3b82f6', CRYPTO: '#f59e0b', REAL_ESTATE: '#8b5cf6', CASH: '#10b981' };
  return <span style={{ fontSize: '0.72rem', fontWeight: 600, color: colors[type] || 'var(--text-muted)', letterSpacing: '0.03em', textTransform: 'uppercase' }}>{type}</span>;
}
