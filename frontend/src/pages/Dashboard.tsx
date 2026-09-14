import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ClipboardList,
  CheckCircle2,
  AlertTriangle,
  Eye,
  TrendingUp,
  ArrowRight,
  RefreshCw,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { getDashboard } from '../api/client';
import { StatusBadge } from '../components/Badges';
import type { DashboardStats } from '../types';

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDashboard();
      setStats(data);
      setBackendOk(true);
    } catch (err: unknown) {
      setBackendOk(false);
      setError('Cannot connect to backend. Make sure the FastAPI server is running on port 8000.');
    } finally {
      setLoading(false);
    }
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
          label: 'Potential Violations',
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
            : 'Backend offline — Start the FastAPI server: cd backend && uvicorn main:app --reload'}
        </div>
      )}

      {/* Page title */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Inspection Dashboard</h2>
          <p className="text-sm mt-1" style={{ color: 'rgba(226,232,240,0.55)' }}>
            Overview of all product compliance inspections
          </p>
        </div>
        <button
          onClick={load}
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
              <div key={card.label} className="stat-card">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs font-medium mb-1" style={{ color: 'rgba(226,232,240,0.55)' }}>
                      {card.label}
                    </p>
                    <p className="text-3xl font-black" style={{ color: card.color }}>
                      {card.value}
                    </p>
                  </div>
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center"
                    style={{ background: card.bg, border: `1px solid ${card.border}` }}
                  >
                    <Icon className="w-5 h-5" style={{ color: card.color }} />
                  </div>
                </div>
                {stats && stats.total > 0 && (
                  <div className="mt-3 flex items-center gap-1">
                    <TrendingUp className="w-3 h-3" style={{ color: card.color, opacity: 0.6 }} />
                    <span className="text-xs" style={{ color: 'rgba(226,232,240,0.4)' }}>
                      {stats.total > 0
                        ? `${Math.round((card.value / stats.total) * 100)}% of total`
                        : '—'}
                    </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Quick action */}
      <div
        className="relative overflow-hidden rounded-2xl p-6 cursor-pointer group"
        style={{
          background: 'linear-gradient(135deg, var(--color-navy-800), var(--color-navy-700))',
          border: '1px solid rgba(212,175,55,0.2)',
        }}
        onClick={() => navigate('/inspect')}
      >
        <div
          className="absolute top-0 right-0 w-64 h-64 rounded-full opacity-5 -translate-y-1/2 translate-x-1/2"
          style={{ background: 'var(--color-gold-500)' }}
        />
        <div className="relative flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white mb-1">Start New Inspection</h3>
            <p className="text-sm" style={{ color: 'rgba(226,232,240,0.55)' }}>
              Upload a product image to begin OCR-based compliance analysis
            </p>
          </div>
          <button className="btn-primary flex items-center gap-2 group-hover:gap-3 transition-all">
            Inspect Now
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Recent inspections */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white">Recent Inspections</h3>
          <button
            className="text-sm flex items-center gap-1"
            style={{ color: 'var(--color-gold-500)' }}
            onClick={() => navigate('/history')}
          >
            View all <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        <div className="glass-card overflow-hidden">
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
                          className="px-4 py-3 text-left text-xs font-semibold tracking-wider"
                          style={{ color: 'rgba(226,232,240,0.45)' }}
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
                      className="table-row-hover"
                      style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}
                      onClick={() => navigate(`/analysis/${insp.inspection_id}`)}
                    >
                      <td className="px-4 py-3 font-mono text-xs" style={{ color: 'var(--color-gold-500)' }}>
                        {insp.inspection_id.slice(0, 24)}...
                      </td>
                      <td className="px-4 py-3 text-white font-medium">
                        {insp.product_name ?? <span style={{ color: 'rgba(226,232,240,0.35)' }}>—</span>}
                        {insp.is_demo && (
                          <span
                            className="ml-2 text-xs px-1.5 py-0.5 rounded"
                            style={{ background: 'rgba(168,85,247,0.15)', color: '#c084fc' }}
                          >
                            DEMO
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3" style={{ color: 'rgba(226,232,240,0.55)' }}>
                        {new Date(insp.created_at).toLocaleDateString('en-IN', {
                          day: '2-digit',
                          month: 'short',
                          year: 'numeric',
                        })}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={insp.status} />
                      </td>
                      <td className="px-4 py-3 text-center">
                        {insp.violation_count > 0 ? (
                          <span className="font-bold" style={{ color: '#fca5a5' }}>
                            {insp.violation_count}
                          </span>
                        ) : (
                          <span style={{ color: 'rgba(226,232,240,0.35)' }}>0</span>
                        )}
                      </td>
                      <td className="px-4 py-3" style={{ color: 'rgba(226,232,240,0.55)' }}>
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

      {/* Prototype disclaimer */}
      <div
        className="rounded-xl p-4 text-xs"
        style={{
          background: 'rgba(245,158,11,0.06)',
          border: '1px solid rgba(245,158,11,0.15)',
          color: 'rgba(252,211,77,0.7)',
        }}
      >
        ⚠️ <strong>PROTOTYPE DISCLAIMER:</strong> SMART-LM is an inspection-assistance tool for
        SIH 2026. It does NOT make official legal determinations. All AI/OCR findings must be
        physically verified by a qualified Legal Metrology Inspector before any enforcement action.
        Compliance rules are prototype references and must be verified against current official GoI
        Legal Metrology documents.
      </div>
    </div>
  );
}
