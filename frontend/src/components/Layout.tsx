import { Link, useLocation } from 'react-router-dom';
import { ReactNode } from 'react';

const NAV_ITEMS = [
  { path: '/screener', label: 'Screener' },
  { path: '/portfolio', label: 'Portfolio' },
  { path: '/journal', label: 'Journal' },
  { path: '/settings', label: 'Settings' },
];

export default function Layout({ children }: { children: ReactNode }) {
  const location = useLocation();

  return (
    <>
      <nav className="nav">
        <div className="container nav__inner">
          <Link to="/" className="nav__brand">MOSI</Link>
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav__link ${location.pathname.startsWith(item.path) ? 'nav__link--active' : ''}`}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </nav>
      <main className="container" style={{ paddingTop: 16, paddingBottom: 32 }}>
        {children}
      </main>
    </>
  );
}
