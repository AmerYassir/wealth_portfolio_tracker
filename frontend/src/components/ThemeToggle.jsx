import { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';
import { applyTheme, getTheme } from '../theme.js';

export default function ThemeToggle() {
  const [theme, setTheme] = useState(getTheme());
  useEffect(() => { applyTheme(theme); }, [theme]);
  return (
    <button
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      style={{ padding: '0.5rem', display: 'flex', alignItems: 'center' }}
    >
      {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
    </button>
  );
}
