import { useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import {
  ClipboardList,
  CheckCircle2,
  AlertTriangle,
  Eye,
  ArrowRight,
  RefreshCw,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { getDashboard } from '../api/client';
import { StatusBadge } from '../components/Badges';
import type { DashboardStats } from '../types';
import { useAuth } from '../context/AuthContext';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const load = async () => {
    try {
      const data = await getDashboard();
      setStats(data);
      setBackendOk(true);
      setLoadError(null);
    } catch (error: unknown) {
      setBackendOk(false);
      if (axios.isAxiosError(error)) {
        const status = error.response?.status;
        if (status === 401) {
          logout();
          navigate('/login', { state: { message: 'Your session expired. Please sign in again.' } });
          return;
        }
        if (status === 403) {
          setLoadError('You do not have permission to view the dashboard.');
          return;
        }
        if (error.response) {
          const detail = error.response.data?.detail;
          setLoadError(typeof detail === 'string' ? detail : `Dashboard request failed (${status}).`);
          return;
        }
      }
      setLoadError('Unable to reach the backend. Check that the API is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  const refresh = () => {
    setLoading(true);
    load();
  };

  useEffect(() => {
    load();
  }, []);

  const statCards = stats
    ? [
        {
          label: 'Total Inspections',
          value: stats.total,
          icon: ClipboardList,
          color: '#60a5fa',
          bg: 'rgba(96,165,250,0.1)',
          border: 'rgba(96,165,250,0.2)',
        },
        {
          label: 'Compliant',
          value: stats.compliant,
          icon: CheckCircle2,
          color: '#6ee7b7',
          bg: 'rgba(110,231,183,0.1)',
          border: 'rgba(110,231,183,0.2)',
        },
        {
          label: 'Violations',
          value: stats.violations,
          icon: AlertTriangle,
          color: '#fca5a5',
          bg: 'rgba(252,165,165,0.1)',
          border: 'rgba(252,165,165,0.2)',
        },
        {
          label: 'Needs Review',
          value: stats.needs_review,
          icon: Eye,
          color: '#fcd34d',
          bg: 'rgba(252,211,77,0.1)',
          border: 'rgba(252,211,77,0.2)',
        },
      ]
    : [];

  const pieData = stats ? [
    { name: 'Compliant', value: stats.compliant, color: '#6ee7b7' },
    { name: 'Violations', value: stats.violations, color: '#fca5a5' },
    { name: 'Review', value: stats.needs_review, color: '#fcd34d' }
  ] : [];

  return (
    <div className="space-y-8">
      {/* Backend status */}
      {backendOk !== null && (
        <div
          className="flex items-center gap-2 text-sm px-4 py-2 rounded-lg"
          style={{
            background: backendOk ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)',
            border: `1px solid ${backendOk ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`,
            color: backendOk ? '#6ee7b7' : '#fca5a5',
          }}
        >
          {backendOk ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
          {backendOk
            ? 'Backend connected — SMART-LM API is online'
            : loadError ?? 'Backend offline — Check API connection'}
        </div>
      )}

      {/* Page title */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Welcome back, {user?.username}</h2>
          <p className="text-sm mt-1" style={{ color: 'rgba(226,232,240,0.55)' }}>
            Overview of product compliance and inspection metrics
          </p>
        </div>
        <button
          onClick={refresh}
          className="flex items-center gap-2 btn-ghost"
          disabled={loading}
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Stat cards */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div
              key={i}
              className="stat-card animate-pulse h-28"
              style={{ background: 'var(--color-navy-800)' }}
            />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {statCards.map((card) => {
            const Icon = card.icon;
            return (
              <div key={card.label} className="stat-card hover:-translate-y-1 transition-transform">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs font-medium mb-1 uppercase tracking-wider" style={{ color: 'rgba(226,232,240,0.55)' }}>
                      {card.label}
                    </p>
                    <p className="text-3xl font-black" style={{ color: card.color }}>
                      {card.value}
                    </p>
                  </div>
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center shadow-lg"
                    style={{ background: card.bg, border: `1px solid ${card.border}`, boxShadow: `0 4px 20px ${card.bg}` }}
                  >
                    <Icon className="w-5 h-5" style={{ color: card.color }} />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Charts Section */}
      {!loading && stats && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="glass-card p-6 col-span-1 border border-slate-700/50">
            <h3 className="text-lg font-bold text-white mb-4">Compliance Breakdown</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} stroke="transparent" />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'rgba(15,23,42,0.9)', borderColor: 'rgba(212,175,55,0.2)', borderRadius: '8px' }}
                    itemStyle={{ color: '#fff' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-4 text-xs mt-2">
              {pieData.map(d => (
                <div key={d.name} className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }}></div>
                  <span className="text-slate-400">{d.name}</span>
                </div>
              ))}
            </div>
          </div>
          
          <div className="glass-card p-6 col-span-1 lg:col-span-2 border border-slate-700/50">
             <h3 className="text-lg font-bold text-white mb-4">Recent Trend (Last 7 Days)</h3>
             <div className="h-64 flex items-center justify-center text-slate-500 border border-dashed border-slate-700 rounded-xl">
               {/* Mock trend chart since backend doesn't provide time-series yet */}
               <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={[
                    { name: 'Mon', compliant: 4, violations: 1 },
                    { name: 'Tue', compliant: 3, violations: 2 },
                    { name: 'Wed', compliant: 5, violations: 0 },
                    { name: 'Thu', compliant: 2, violations: 1 },
                    { name: 'Fri', compliant: 6, violations: 3 },
                    { name: 'Sat', compliant: 4, violations: 0 },
                    { name: 'Sun', compliant: 7, violations: 1 }
                  ]}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                    <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: 'rgba(15,23,42,0.9)', borderColor: 'rgba(212,175,55,0.2)', borderRadius: '8px' }} />
                    <Bar dataKey="compliant" fill="#6ee7b7" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="violations" fill="#fca5a5" radius={[4, 4, 0, 0]} />
                  </BarChart>
               </ResponsiveContainer>
             </div>
          </div>
        </div>
      )}

      {/* Recent inspections */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white">Recent Inspections</h3>
          <button
            className="text-sm flex items-center gap-1 hover:gap-2 transition-all"
            style={{ color: 'var(--color-gold-500)' }}
            onClick={() => navigate('/history')}
          >
            View all <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        <div className="glass-card overflow-hidden border border-slate-700/50">
          {!stats || stats.recent.length === 0 ? (
            <div className="p-12 text-center" style={{ color: 'rgba(226,232,240,0.4)' }}>
              <ClipboardList className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="font-medium">No inspections yet</p>
              <p className="text-sm mt-1">Upload a product image to begin</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(212,175,55,0.1)' }}>
                    {['Inspection ID', 'Product', 'Date', 'Status', 'Violations', 'Confidence'].map(
                      (h) => (
                        <th
                          key={h}
                          className="px-4 py-4 text-left text-xs font-semibold tracking-wider uppercase text-slate-400 bg-slate-900/40"
                        >
                          {h}
                        </th>
                      )
                    )}
                  </tr>
                </thead>
                <tbody>
                  {stats.recent.map((insp) => (
                    <tr
                      key={insp.inspection_id}
                      className="table-row-hover hover:bg-slate-800/30 transition-colors cursor-pointer"
                      style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}
                      onClick={() => navigate(`/analysis/${insp.inspection_id}`)}
                    >
                      <td className="px-4 py-4 font-mono text-xs" style={{ color: 'var(--color-gold-500)' }}>
                        {insp.inspection_id.slice(0, 18)}...
                      </td>
                      <td className="px-4 py-4 text-white font-medium">
                        {insp.product_name ?? <span style={{ color: 'rgba(226,232,240,0.35)' }}>—</span>}
                      </td>
                      <td className="px-4 py-4" style={{ color: 'rgba(226,232,240,0.55)' }}>
                        {new Date(insp.created_at).toLocaleDateString('en-IN', {
                          day: '2-digit',
                          month: 'short',
                        })}
                      </td>
                      <td className="px-4 py-4">
                        <StatusBadge status={insp.status} />
                      </td>
                      <td className="px-4 py-4 text-center">
                        {insp.violation_count > 0 ? (
                          <span className="font-bold inline-flex items-center justify-center w-6 h-6 rounded-full bg-red-500/20 text-red-400">
                            {insp.violation_count}
                          </span>
                        ) : (
                          <span style={{ color: 'rgba(226,232,240,0.35)' }}>0</span>
                        )}
                      </td>
                      <td className="px-4 py-4" style={{ color: 'rgba(226,232,240,0.55)' }}>
                        {insp.overall_confidence ?? '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
