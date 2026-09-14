import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  ScanLine,
  History,
  Shield,
  Menu,
  X,
  Scale,
} from 'lucide-react';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/inspect', icon: ScanLine, label: 'New Inspection' },
  { path: '/history', icon: History, label: 'History' },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex min-h-screen" style={{ backgroundColor: 'var(--color-navy-950)' }}>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 z-30 transform transition-transform duration-300
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 lg:static lg:z-auto`}
        style={{
          background: 'linear-gradient(180deg, var(--color-navy-900) 0%, var(--color-navy-950) 100%)',
          borderRight: '1px solid rgba(212,175,55,0.15)',
        }}
      >
        {/* Logo */}
        <div
          className="flex items-center gap-3 px-6 py-5"
          style={{ borderBottom: '1px solid rgba(212,175,55,0.12)' }}
        >
          <div
            className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ background: 'linear-gradient(135deg, var(--color-gold-500), var(--color-gold-400))' }}
          >
            <Scale className="w-5 h-5" style={{ color: 'var(--color-navy-900)' }} />
          </div>
          <div>
            <div className="font-black text-sm tracking-widest" style={{ color: 'var(--color-gold-500)' }}>
              SMART-LM
            </div>
            <div className="text-xs" style={{ color: 'rgba(226,232,240,0.5)' }}>
              Legal Metrology
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="mt-6 px-3">
          {navItems.map((item) => {
            const active = location.pathname === item.path;
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className="flex items-center gap-3 px-4 py-3 rounded-lg mb-1 transition-all duration-200"
                style={{
                  background: active ? 'rgba(212,175,55,0.12)' : 'transparent',
                  color: active ? 'var(--color-gold-500)' : 'rgba(226,232,240,0.7)',
                  borderLeft: active ? '3px solid var(--color-gold-500)' : '3px solid transparent',
                }}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                <span className="text-sm font-medium">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Bottom badge */}
        <div className="absolute bottom-0 left-0 right-0 px-4 py-4">
          <div
            className="rounded-lg px-3 py-2 text-center"
            style={{ background: 'rgba(212,175,55,0.07)', border: '1px solid rgba(212,175,55,0.12)' }}
          >
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <Shield className="w-3.5 h-3.5" style={{ color: 'var(--color-gold-500)' }} />
              <span className="text-xs font-semibold" style={{ color: 'var(--color-gold-500)' }}>
                SIH 2026 Prototype
              </span>
            </div>
            <p className="text-xs" style={{ color: 'rgba(226,232,240,0.4)' }}>
              Not for enforcement use
            </p>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header
          className="flex items-center justify-between px-4 lg:px-8 py-4 sticky top-0 z-10"
          style={{
            background: 'rgba(6,13,26,0.95)',
            backdropFilter: 'blur(12px)',
            borderBottom: '1px solid rgba(212,175,55,0.1)',
          }}
        >
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden p-2 rounded-lg transition-colors"
              style={{ color: 'rgba(226,232,240,0.7)' }}
            >
              {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
            <div>
              <h1 className="text-base font-bold" style={{ color: '#e2e8f0' }}>
                {navItems.find((n) => n.path === location.pathname)?.label ?? 'SMART-LM'}
              </h1>
              <p className="text-xs" style={{ color: 'rgba(226,232,240,0.45)' }}>
                Smart Legal Metrology Compliance & Inspection System
              </p>
            </div>
          </div>
          <div
            className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium"
            style={{
              background: 'rgba(212,175,55,0.1)',
              border: '1px solid rgba(212,175,55,0.2)',
              color: 'var(--color-gold-500)',
            }}
          >
            <Shield className="w-3.5 h-3.5" />
            Inspection Mode
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 p-4 lg:p-8 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
