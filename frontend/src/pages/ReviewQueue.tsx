import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Clock, AlertCircle } from 'lucide-react';
import { StatusBadge } from '../components/Badges';
import type { InspectionSummary } from '../types';
import { getReviewQueue } from '../api/client';

export default function ReviewQueue() {
  const [queue, setQueue] = useState<InspectionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const loadQueue = async () => {
    setLoading(true);
    try {
      setQueue(await getReviewQueue());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch review queue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white">Review Queue</h2>
        <p className="text-sm mt-1" style={{ color: 'rgba(226,232,240,0.55)' }}>
          Inspections requiring human review due to poor image quality or OCR failure
        </p>
      </div>

      {error && (
        <div className="flex items-start gap-3 rounded-xl p-4 bg-red-500/10 border border-red-500/20">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-red-400" />
          <div>
            <p className="text-sm font-medium text-red-400">Error loading queue</p>
            <p className="text-sm mt-0.5 text-red-300/80">{error}</p>
          </div>
        </div>
      )}

      <div className="glass-card overflow-hidden border border-slate-700/50">
        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading queue...</div>
        ) : queue.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <CheckCircle className="w-12 h-12 mx-auto mb-3 opacity-30 text-emerald-500" />
            <p className="font-medium text-white">All caught up!</p>
            <p className="text-sm mt-1">There are no inspections waiting for review.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700 bg-slate-900/40 text-slate-400">
                  <th className="px-6 py-4 text-left font-semibold tracking-wider uppercase text-xs">Inspection ID</th>
                  <th className="px-6 py-4 text-left font-semibold tracking-wider uppercase text-xs">Product</th>
                  <th className="px-6 py-4 text-left font-semibold tracking-wider uppercase text-xs">Date</th>
                  <th className="px-6 py-4 text-left font-semibold tracking-wider uppercase text-xs">Status</th>
                  <th className="px-6 py-4 text-right font-semibold tracking-wider uppercase text-xs">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {queue.map((insp) => (
                  <tr key={insp.inspection_id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4 font-mono text-xs text-blue-400">
                      {insp.inspection_id.slice(0, 24)}...
                    </td>
                    <td className="px-6 py-4 font-medium text-white">
                      {insp.product_name || <span className="text-slate-500">—</span>}
                    </td>
                    <td className="px-6 py-4 text-slate-400">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5" />
                        {new Date(insp.created_at).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={insp.status} />
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button 
                        onClick={() => navigate(`/analysis/${insp.inspection_id}`)}
                        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 rounded-lg font-medium transition-colors border border-blue-500/20"
                      >
                        Review <ArrowRight className="w-4 h-4" />
                      </button>
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

function CheckCircle(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  );
}
