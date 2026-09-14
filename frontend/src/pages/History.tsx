import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  History as HistoryIcon,
  RefreshCw,
  ArrowRight,
  Search,
  ClipboardList,
} from 'lucide-react';
import { listInspections } from '../api/client';
import { StatusBadge } from '../components/Badges';
import type { InspectionSummary } from '../types';

export default function History() {
  const [inspections, setInspections] = useState<InspectionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listInspections();
      setInspections(data);
    } catch {
      setError('Could not load inspections. Check that the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const filtered = inspections.filter((i) => {
    const q = search.toLowerCase();
    return (
      i.inspection_id.toLowerCase().includes(q) ||
      (i.product_name ?? '').toLowerCase().includes(q) ||
      i.status.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <HistoryIcon className="w-6 h-6" style={{ color: 'var(--color-gold-500)' }} />
            Inspection History
          </h2>
          <p className="text-sm mt-1" style={{ color: 'rgba(226,232,240,0.55)' }}>
            {inspections.length} inspection{inspections.length !== 1 ? 's' : ''} recorded
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4"
              style={{ color: 'rgba(226,232,240,0.35)' }}
            />
            <input
              type="text"
              placeholder="Search inspections..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input-field pl-9"
              style={{ width: '220px' }}
            />
          </div>
          <button
            onClick={load}
            className="btn-ghost flex items-center gap-2"
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div
          className="rounded-xl p-4 text-sm"
          style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#fca5a5' }}
        >
          {error}
        </div>
      )}

      <div className="glass-card overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <RefreshCw className="w-8 h-8 mx-auto animate-spin mb-3" style={{ color: 'var(--color-gold-500)' }} />
            <p className="text-sm" style={{ color: 'rgba(226,232,240,0.45)' }}>Loading...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center" style={{ color: 'rgba(226,232,240,0.4)' }}>
            <ClipboardList className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="font-medium">{search ? 'No matching inspections' : 'No inspections yet'}</p>
            {!search && (
              <button
                className="btn-primary mt-4"
                onClick={() => navigate('/inspect')}
              >
                Start First Inspection
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(212,175,55,0.1)' }}>
                  {[
                    'Inspection ID',
                    'Product Name',
                    'Date',
                    'Image Quality',
                    'Status',
                    'Violations',
                    'Confidence',
                    '',
                  ].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-xs font-semibold tracking-wider"
                      style={{ color: 'rgba(226,232,240,0.45)' }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((insp) => (
                  <tr
                    key={insp.inspection_id}
                    className="table-row-hover"
                    style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}
                    onClick={() => navigate(`/analysis/${insp.inspection_id}`)}
                  >
                    <td className="px-4 py-3">
                      <span className="font-mono text-xs" style={{ color: 'var(--color-gold-500)' }}>
                        {insp.inspection_id.slice(0, 20)}...
                      </span>
                      {insp.is_demo && (
                        <span
                          className="ml-1 text-xs px-1 py-0.5 rounded"
                          style={{ background: 'rgba(168,85,247,0.15)', color: '#c084fc' }}
                        >
                          DEMO
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-white font-medium max-w-xs truncate">
                      {insp.product_name ?? (
                        <span style={{ color: 'rgba(226,232,240,0.3)' }}>—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs whitespace-nowrap" style={{ color: 'rgba(226,232,240,0.55)' }}>
                      {new Date(insp.created_at).toLocaleDateString('en-IN', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric',
                      })}
                      <br />
                      <span style={{ color: 'rgba(226,232,240,0.35)' }}>
                        {new Date(insp.created_at).toLocaleTimeString('en-IN', {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className="text-xs font-medium px-2 py-0.5 rounded"
                        style={{
                          background:
                            insp.image_quality === 'GOOD'
                              ? 'rgba(16,185,129,0.1)'
                              : insp.image_quality === 'ACCEPTABLE'
                              ? 'rgba(245,158,11,0.1)'
                              : 'rgba(239,68,68,0.1)',
                          color:
                            insp.image_quality === 'GOOD'
                              ? '#6ee7b7'
                              : insp.image_quality === 'ACCEPTABLE'
                              ? '#fcd34d'
                              : '#fca5a5',
                        }}
                      >
                        {insp.image_quality ?? '—'}
                      </span>
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
                        <span style={{ color: 'rgba(226,232,240,0.3)' }}>0</span>
                      )}
                    </td>
                    <td className="px-4 py-3" style={{ color: 'rgba(226,232,240,0.55)' }}>
                      {insp.overall_confidence ?? '—'}
                    </td>
                    <td className="px-4 py-3">
                      <ArrowRight className="w-4 h-4" style={{ color: 'rgba(212,175,55,0.5)' }} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
