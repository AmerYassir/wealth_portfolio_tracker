import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Briefcase, ChevronRight, Loader2, LogOut } from 'lucide-react';
import { api } from '../api/client.js';
import { clearTokens } from '../auth.js';

const ROLE_BADGES = {
  OWNER: { label: 'Owner', bg: 'var(--accent-soft)', color: 'var(--accent)' },
  EDITOR: { label: 'Editor', bg: 'rgba(59,130,246,0.12)', color: '#3b82f6' },
  VIEWER: { label: 'Viewer', bg: 'var(--bg-elev-2)', color: 'var(--text-muted)' },
};

export default function PortfolioList() {
  const [portfolios, setPortfolios] = useState(null);
  const [error, setError] = useState(null);
  const nav = useNavigate();

  useEffect(() => {
    api.listPortfolios().then(setPortfolios).catch((e) => setError(e.message));
  }, []);

  function logout() { clearTokens(); nav('/login'); }

  return (
    <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '1.5rem' }}>
        <div>
          <h1>Portfolios</h1>
          <p style={{ color: 'var(--text-muted)', margin: '0.25rem 0 0', fontSize: '0.9rem' }}>
            {portfolios ? `${portfolios.length} portfolio${portfolios.length !== 1 ? 's' : ''}` : 'Loading…'}
          </p>
        </div>
        <button onClick={logout} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <LogOut size={15} /> Sign out
        </button>
      </div>

      {error && <div style={{ background: 'var(--danger-soft)', color: 'var(--danger)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)' }}>{error}</div>}

      {portfolios === null ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
          <Loader2 size={24} style={{ animation: 'spin 1s linear infinite', color: 'var(--text-muted)' }} />
        </div>
      ) : portfolios.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '4rem 1rem', color: 'var(--text-muted)' }}>
          <Briefcase size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
          <p>No portfolios yet.</p>
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
          gap: '1rem',
        }}>
          {portfolios.map((p, i) => {
            const badge = ROLE_BADGES[p.role] || ROLE_BADGES.VIEWER;
            return (
              <Link key={p.id} to={`/portfolios/${p.id}`}
                style={{
                  display: 'block', background: 'var(--bg-elev)', border: '1px solid var(--border)',
                  borderRadius: 'var(--radius)', padding: '1.25rem', color: 'var(--text)',
                  transition: 'transform 0.15s, border-color 0.15s, box-shadow 0.15s',
                  animation: `fadeIn 0.3s ease-out ${i * 0.05}s both`,
                }}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--border-strong)'; e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = 'var(--shadow-md)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = 'none'; }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                  <div style={{
                    width: 38, height: 38, borderRadius: 10, background: 'var(--accent-soft)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent)',
                  }}><Briefcase size={18} /></div>
                  <span style={{
                    fontSize: '0.7rem', fontWeight: 600, padding: '0.2rem 0.55rem',
                    borderRadius: 999, background: badge.bg, color: badge.color,
                    letterSpacing: '0.03em', textTransform: 'uppercase',
                  }}>{badge.label}</span>
                </div>
                <h3 style={{ fontSize: '1.05rem', marginBottom: '0.2rem' }}>{p.name}</h3>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.75rem' }}>
                  <span>Open portfolio</span>
                  <ChevronRight size={16} />
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
