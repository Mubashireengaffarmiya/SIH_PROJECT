import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  ScanLine,
  History,
  Shield,
  Menu,
  X,
  Scale,
  LogOut,
  Users,
  Settings,
  ClipboardList,
  BarChart,
  User
} from 'lucide-react';

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getNavItems = () => {
    const role = user?.role || '';
    const items = [
      { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', roles: ['INSPECTOR', 'REVIEWER', 'ADMIN'] },
      { path: '/inspect', icon: ScanLine, label: 'New Inspection', roles: ['INSPECTOR', 'ADMIN'] },
      { path: '/review-queue', icon: ClipboardList, label: 'Review Queue', roles: ['REVIEWER', 'ADMIN'] },
      { path: '/history', icon: History, label: 'History', roles: ['INSPECTOR', 'REVIEWER', 'ADMIN'] },
      { path: '/admin/users', icon: Users, label: 'User Management', roles: ['ADMIN'] },
      { path: '/admin/rules', icon: Settings, label: 'Rules Engine', roles: ['ADMIN'] },
      { path: '/admin/audit', icon: Shield, label: 'Audit Logs', roles: ['ADMIN'] },
      { path: '/admin/analytics', icon: BarChart, label: 'Analytics', roles: ['ADMIN'] },
    ];
    return items.filter(item => item.roles.includes(role));
  };

  const navItems = getNavItems();

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
            const active = location.pathname.startsWith(item.path);
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
                {navItems.find((n) => location.pathname.startsWith(n.path))?.label ?? 'SMART-LM'}
              </h1>
              <p className="text-xs hidden sm:block" style={{ color: 'rgba(226,232,240,0.45)' }}>
                Smart Legal Metrology Compliance System
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            {user && (
              <div className="flex items-center gap-3 bg-slate-800/50 px-3 py-1.5 rounded-full border border-slate-700/50">
                <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center">
                  <User className="w-4 h-4 text-blue-400" />
                </div>
                <div className="hidden sm:block">
                  <div className="text-sm font-medium text-slate-200">{user.username}</div>
                  <div className="text-[10px] uppercase tracking-wider text-blue-400 font-semibold">{user.role}</div>
                </div>
              </div>
            )}
            
            <button 
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              <span className="text-sm font-medium hidden sm:block">Logout</span>
            </button>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 p-4 lg:p-8 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
