import { BrowserRouter, Navigate, Route, Routes, Link } from 'react-router-dom';
import { Wallet } from 'lucide-react';
import Login from './pages/Login.jsx';
import Signup from './pages/Signup.jsx';
import PortfolioList from './pages/PortfolioList.jsx';
import PortfolioDetail from './pages/PortfolioDetail.jsx';
import ThemeToggle from './components/ThemeToggle.jsx';
import { isLoggedIn } from './auth.js';

function RequireAuth({ children }) {
  if (!isLoggedIn()) return <Navigate to="/login" replace />;
  return children;
}

function TopBar() {
  const logged = isLoggedIn();
  return (
    <header style={{ borderBottom: '1px solid var(--border)', background: 'var(--bg-elev)', padding: '0.85rem 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'sticky', top: 0, zIndex: 10 }}>
      <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', color: 'var(--text)' }}>
        <div style={{ width: 30, height: 30, borderRadius: 8, background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}><Wallet size={17} /></div>
        <span style={{ fontWeight: 600 }}>Wealth Tracker</span>
      </Link>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <ThemeToggle />
        {logged && <Link to="/" style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Portfolios</Link>}
      </div>
    </header>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <TopBar />
        <main style={{ flex: 1, padding: '2rem 1.5rem', maxWidth: 1100, width: '100%', margin: '0 auto' }}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/" element={<RequireAuth><PortfolioList /></RequireAuth>} />
            <Route path="/portfolios/:id" element={<RequireAuth><PortfolioDetail /></RequireAuth>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
