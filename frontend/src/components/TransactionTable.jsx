export default function TransactionTable({ transactions, assetById }) {
  if (!transactions.length) {
    return <p style={{ color: 'var(--text-muted)', padding: '1.5rem 0' }}>No transactions.</p>;
  }
  return (
    <div style={{ background: 'var(--bg-elev)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ background: 'var(--bg-elev-2)', borderBottom: '1px solid var(--border)' }}>
            <Th>Date</Th><Th>Asset</Th><Th>Type</Th><Th align="right">Amount</Th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((t) => (
            <tr key={t.id} style={{ borderBottom: '1px solid var(--border)' }}>
              <Td>{new Date(t.occurred_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}</Td>
              <Td>{assetById[t.asset] || `#${t.asset}`}</Td>
              <Td><TypePill type={t.type} /></Td>
              <Td align="right" className="num">${Number(t.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}</Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Th({ children, align = 'left' }) {
  return <th style={{ textAlign: align, padding: '0.7rem 1rem', fontSize: '0.75rem', fontWeight: 500, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{children}</th>;
}
function Td({ children, align = 'left', className = '' }) {
  return <td className={className} style={{ textAlign: align, padding: '0.75rem 1rem', fontSize: '0.9rem' }}>{children}</td>;
}
function TypePill({ type }) {
  const colors = { BUY: '#10b981', SELL: '#f43f5e', DIVIDEND: '#3b82f6' };
  return <span style={{ fontSize: '0.72rem', fontWeight: 600, color: colors[type] || 'var(--text-muted)', letterSpacing: '0.03em' }}>{type}</span>;
}
