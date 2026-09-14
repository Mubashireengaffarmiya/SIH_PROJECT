import { useEffect, useState } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Download,
  FileText,
  Image as ImageIcon,
  CheckCircle,
  AlertTriangle,
  Eye,
  Package,
  Cpu,
  FileSearch,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { getInspection, downloadPdfReport, downloadDocxReport } from '../api/client';
import { StatusBadge, ConfidenceBadge, SeverityBadge } from '../components/Badges';
import type { AnalysisResponse, InspectionDetail } from '../types';
import { useAuth } from '../context/AuthContext';

type Tab = 'overview' | 'extracted' | 'compliance' | 'violations' | 'reports';

// Field display names
const FIELD_LABELS: Record<string, string> = {
  product_name: 'Product Name',
  mrp: 'MRP',
  net_quantity: 'Net Quantity',
  manufacturer: 'Manufacturer / Packer',
  manufacturing_date: 'Manufacturing Date',
  consumer_care: 'Consumer Care',
  country_of_origin: 'Country of Origin',
  best_before: 'Best Before / Expiry',
  unit_sale_price: 'Unit Sale Price',
};

export default function AnalysisResult() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();

  // Result can come from navigation state (just analyzed) or fetched from DB
  const [result, setResult] = useState<AnalysisResponse | null>(
    (location.state as { result?: AnalysisResponse })?.result ?? null
  );
  const [detail, setDetail] = useState<InspectionDetail | null>(null);
  const [loading, setLoading] = useState(!result);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [downloading, setDownloading] = useState<'pdf' | 'docx' | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    if (!id) return;
    const fetchDetail = async () => {
      try {
        const d = await getInspection(id);
        setDetail(d);
        if (!result) setLoading(false);
      } catch {
        if (!result) {
          setError('Inspection not found.');
          setLoading(false);
        }
      }
    };
    fetchDetail();
  }, [id]);

  const inspection = detail;
  const status = result?.compliance.overall_status ?? inspection?.status ?? 'NEEDS_HUMAN_REVIEW';
  const confidence = result?.compliance.overall_confidence ?? inspection?.overall_confidence ?? 'LOW';
  const violations = result?.compliance.violations ?? inspection?.violations ?? [];
  const declarations = result
    ? ([
        'product_name', 'mrp', 'net_quantity', 'manufacturer', 'manufacturing_date',
        'consumer_care', 'country_of_origin', 'best_before', 'unit_sale_price',
      ] as const).map((key) => ({
        field_name: key,
        extracted_value: result.extraction[key].value,
        confidence: result.extraction[key].confidence,
        evidence_text: result.extraction[key].evidence_text,
        status: null,
      }))
    : inspection?.declarations ?? [];

  const imageUrl = result
    ? null // we'll show local preview via state
    : inspection?.image_path
    ? `http://localhost:8000${inspection.image_path}`
    : null;

  const localPreviewUrl = (location.state as { previewUrl?: string })?.previewUrl ?? null;
  const effectiveImageUrl = localPreviewUrl ?? imageUrl;

  const handleDownload = async (type: 'pdf' | 'docx') => {
    if (!id) return;
    setDownloading(type);
    try {
      if (type === 'pdf') await downloadPdfReport(id);
      else await downloadDocxReport(id);
    } catch (e) {
      alert('Report generation failed. Make sure the backend is running.');
    } finally {
      setDownloading(null);
    }
  };

  const handleReviewAction = async (action: string) => {
    if (!id) return;
    setActionLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/reviewer/inspections/${id}/review`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ action, comment: '' })
      });
      if (!res.ok) throw new Error('Action failed');
      // Reload inspection
      const d = await getInspection(id);
      setDetail(d);
      setResult(null); // Clear local result to use DB data
    } catch (err: any) {
      alert(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin" style={{ color: 'var(--color-gold-500)' }} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto pt-8">
        <div className="glass-card p-8 text-center">
          <AlertCircle className="w-12 h-12 mx-auto mb-3" style={{ color: '#fca5a5' }} />
          <p className="text-white font-semibold">{error}</p>
          <button className="btn-primary mt-4" onClick={() => navigate('/history')}>
            Back to History
          </button>
        </div>
      </div>
    );
  }

  const tabs: { key: Tab; label: string; count?: number }[] = [
    { key: 'overview', label: 'Overview' },
    { key: 'extracted', label: 'Declarations', count: declarations.length },
    { key: 'compliance', label: 'Compliance' },
    { key: 'violations', label: 'Violations', count: violations.length },
    { key: 'reports', label: 'Reports' },
  ];

  return (
    <div className="space-y-6">
      {/* Back nav */}
      <button
        className="flex items-center gap-2 text-sm transition-colors"
        style={{ color: 'rgba(226,232,240,0.55)' }}
        onClick={() => navigate(-1)}
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </button>

      {/* Status banner */}
      <div
        className="rounded-2xl p-6"
        style={{
          background:
            status === 'VERIFIED_COMPLIANT'
              ? 'linear-gradient(135deg, rgba(16,185,129,0.12), rgba(16,185,129,0.05))'
              : status === 'POTENTIAL_VIOLATION'
              ? 'linear-gradient(135deg, rgba(239,68,68,0.12), rgba(239,68,68,0.05))'
              : 'linear-gradient(135deg, rgba(245,158,11,0.12), rgba(245,158,11,0.05))',
          border:
            status === 'VERIFIED_COMPLIANT'
              ? '1px solid rgba(16,185,129,0.25)'
              : status === 'POTENTIAL_VIOLATION'
              ? '1px solid rgba(239,68,68,0.25)'
              : '1px solid rgba(245,158,11,0.25)',
        }}
      >
        <div className="flex flex-wrap items-center gap-4">
          <div>
            {status === 'VERIFIED_COMPLIANT' && (
              <CheckCircle className="w-10 h-10" style={{ color: '#6ee7b7' }} />
            )}
            {status === 'POTENTIAL_VIOLATION' && (
              <AlertTriangle className="w-10 h-10" style={{ color: '#fca5a5' }} />
            )}
            {status === 'NEEDS_HUMAN_REVIEW' && (
              <Eye className="w-10 h-10" style={{ color: '#fcd34d' }} />
            )}
          </div>
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-3 mb-1">
              <StatusBadge status={status as 'VERIFIED_COMPLIANT' | 'POTENTIAL_VIOLATION' | 'NEEDS_HUMAN_REVIEW'} />
              <ConfidenceBadge confidence={confidence} />
            </div>
            <p className="text-white font-bold text-lg">
              {status === 'VERIFIED_COMPLIANT' && 'All detected declarations verified'}
              {status === 'POTENTIAL_VIOLATION' && 'Potential compliance issues detected'}
              {status === 'NEEDS_HUMAN_REVIEW' && 'Human review required'}
            </p>
            <p className="text-sm mt-1" style={{ color: 'rgba(226,232,240,0.55)' }}>
              {result?.compliance.summary ?? '—'}
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs" style={{ color: 'rgba(226,232,240,0.4)' }}>Inspection ID</p>
            <p className="font-mono text-xs font-bold" style={{ color: 'var(--color-gold-500)' }}>
              {id}
            </p>
          </div>
        </div>
        
        {/* Reviewer Actions */}
        {status === 'NEEDS_HUMAN_REVIEW' && ['REVIEWER', 'ADMIN'].includes(user?.role || '') && (
          <div className="mt-6 pt-6 border-t border-slate-700/50 flex flex-wrap gap-4">
            <button 
              onClick={() => handleReviewAction('CONFIRM')}
              disabled={actionLoading}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-lg hover:bg-emerald-500/20 transition-colors"
            >
              <CheckCircle className="w-4 h-4" /> Confirm Compliant
            </button>
            <button 
              onClick={() => handleReviewAction('REJECT')}
              disabled={actionLoading}
              className="flex items-center gap-2 px-4 py-2 bg-red-500/10 text-red-400 border border-red-500/20 rounded-lg hover:bg-red-500/20 transition-colors"
            >
              <AlertTriangle className="w-4 h-4" /> Mark as Violation
            </button>
            <button 
              onClick={() => handleReviewAction('RETAKE')}
              disabled={actionLoading}
              className="flex items-center gap-2 px-4 py-2 bg-slate-700/50 text-slate-300 border border-slate-600/50 rounded-lg hover:bg-slate-700 transition-colors"
            >
              Request Retake
            </button>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 overflow-x-auto pb-1" style={{ borderBottom: '1px solid rgba(212,175,55,0.1)' }}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className="px-4 py-2.5 text-sm font-medium rounded-t-lg transition-all whitespace-nowrap flex items-center gap-1.5"
            style={{
              background: activeTab === tab.key ? 'rgba(212,175,55,0.1)' : 'transparent',
              color: activeTab === tab.key ? 'var(--color-gold-500)' : 'rgba(226,232,240,0.5)',
              borderBottom: activeTab === tab.key ? '2px solid var(--color-gold-500)' : '2px solid transparent',
            }}
          >
            {tab.label}
            {tab.count !== undefined && (
              <span
                className="text-xs px-1.5 py-0.5 rounded-full"
                style={{
                  background: tab.count > 0 ? 'rgba(239,68,68,0.2)' : 'rgba(255,255,255,0.08)',
                  color: tab.count > 0 ? '#fca5a5' : 'rgba(226,232,240,0.4)',
                }}
              >
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Image */}
            <div className="glass-card p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <ImageIcon className="w-4 h-4" style={{ color: 'var(--color-gold-500)' }} />
                Product Image
              </h3>
              {effectiveImageUrl ? (
                <img
                  src={effectiveImageUrl}
                  alt="Inspected product"
                  className="w-full rounded-lg object-contain"
                  style={{ maxHeight: '380px', background: '#0a0a0a' }}
                />
              ) : (
                <div
                  className="h-48 rounded-lg flex items-center justify-center"
                  style={{ background: 'rgba(255,255,255,0.04)' }}
                >
                  <p className="text-sm" style={{ color: 'rgba(226,232,240,0.3)' }}>
                    Image not available
                  </p>
                </div>
              )}
              {result && (
                <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                  {[
                    { label: 'Quality', value: result.image_quality.quality },
                    { label: 'Blur Score', value: result.image_quality.blur_score.toFixed(1) },
                    { label: 'Brightness', value: result.image_quality.brightness.toFixed(1) },
                  ].map((m) => (
                    <div
                      key={m.label}
                      className="rounded-lg p-2 text-center"
                      style={{ background: 'rgba(255,255,255,0.04)' }}
                    >
                      <p style={{ color: 'rgba(226,232,240,0.4)' }}>{m.label}</p>
                      <p className="font-bold text-white mt-0.5">{m.value}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Quick summary */}
            <div className="space-y-4">
              {result && (
                <div className="glass-card p-4">
                  <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                    <Cpu className="w-4 h-4" style={{ color: 'var(--color-gold-500)' }} />
                    OCR Engine
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span style={{ color: 'rgba(226,232,240,0.5)' }}>Engine</span>
                      <span className="font-medium text-white">{result.ocr.engine}</span>
                    </div>
                    <div className="flex justify-between">
                      <span style={{ color: 'rgba(226,232,240,0.5)' }}>Success</span>
                      <span className={result.ocr.success ? 'text-green-400' : 'text-red-400'}>
                        {result.ocr.success ? '✓ Yes' : '✗ No'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span style={{ color: 'rgba(226,232,240,0.5)' }}>Words detected</span>
                      <span className="font-medium text-white">{result.ocr.words.length}</span>
                    </div>
                    {result.ocr.error && (
                      <p className="text-xs mt-2 p-2 rounded" style={{ background: 'rgba(239,68,68,0.1)', color: '#fca5a5' }}>
                        {result.ocr.error}
                      </p>
                    )}
                  </div>
                </div>
              )}

              <div className="glass-card p-4">
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <Package className="w-4 h-4" style={{ color: 'var(--color-gold-500)' }} />
                  Key Declarations
                </h3>
                <div className="space-y-2">
                  {(['product_name', 'mrp', 'net_quantity', 'manufacturer'] as const).map((key) => {
                    const field = result?.extraction[key];
                    const val = field?.value;
                    return (
                      <div key={key} className="flex justify-between items-start gap-2">
                        <span className="text-xs" style={{ color: 'rgba(226,232,240,0.45)' }}>
                          {FIELD_LABELS[key]}
                        </span>
                        <span
                          className="text-xs font-medium text-right max-w-[60%]"
                          style={{ color: val ? '#e2e8f0' : 'rgba(226,232,240,0.25)' }}
                        >
                          {val ?? 'Not detected'}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'extracted' && (
          <div className="glass-card overflow-hidden">
            <div className="p-4 border-b" style={{ borderColor: 'rgba(212,175,55,0.1)' }}>
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <FileSearch className="w-4 h-4" style={{ color: 'var(--color-gold-500)' }} />
                Extracted Declarations
              </h3>
              <p className="text-xs mt-1" style={{ color: 'rgba(226,232,240,0.4)' }}>
                Not detected = field not found in OCR output. Does NOT mean legally absent.
              </p>
            </div>
            <div className="divide-y" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
              {declarations.map((d) => (
                <div key={d.field_name} className="px-4 py-4 flex flex-wrap gap-3 items-start">
                  <div className="w-36 flex-shrink-0">
                    <p className="text-xs font-semibold" style={{ color: 'rgba(226,232,240,0.7)' }}>
                      {FIELD_LABELS[d.field_name] ?? d.field_name.replace('_', ' ')}
                    </p>
                  </div>
                  <div className="flex-1">
                    <p
                      className="text-sm font-medium"
                      style={{ color: d.extracted_value ? '#e2e8f0' : 'rgba(226,232,240,0.25)' }}
                    >
                      {d.extracted_value ?? 'Not detected'}
                    </p>
                    {d.evidence_text && (
                      <p className="text-xs mt-1 font-mono" style={{ color: 'rgba(226,232,240,0.35)' }}>
                        Evidence: "{d.evidence_text.slice(0, 80)}"
                      </p>
                    )}
                  </div>
                  <ConfidenceBadge confidence={d.confidence ?? 'LOW'} />
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'compliance' && result && (
          <div className="space-y-4">
            <div className="glass-card p-5">
              <h3 className="text-sm font-semibold text-white mb-4">Rule Check Results</h3>
              <div className="space-y-2">
                {Object.entries(result.compliance.field_statuses).map(([ruleId, status]) => (
                  <div
                    key={ruleId}
                    className="flex items-center justify-between p-3 rounded-lg"
                    style={{ background: 'rgba(255,255,255,0.03)' }}
                  >
                    <span className="text-xs font-mono" style={{ color: 'rgba(226,232,240,0.55)' }}>
                      {ruleId}
                    </span>
                    <StatusBadge status={status as 'VERIFIED_COMPLIANT' | 'POTENTIAL_VIOLATION' | 'NEEDS_HUMAN_REVIEW'} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'violations' && (
          <div className="space-y-4">
            {violations.length === 0 ? (
              <div className="glass-card p-12 text-center">
                <CheckCircle className="w-12 h-12 mx-auto mb-3" style={{ color: '#6ee7b7' }} />
                <p className="text-white font-semibold">No violations flagged</p>
                <p className="text-sm mt-1" style={{ color: 'rgba(226,232,240,0.4)' }}>
                  All checked declarations were found or are within review bounds
                </p>
              </div>
            ) : (
              violations.map((v, i) => (
                <div
                  key={i}
                  className="glass-card p-5"
                  style={{
                    borderLeft: `3px solid ${v.severity === 'HIGH' ? '#f87171' : v.severity === 'MEDIUM' ? '#fbbf24' : '#60a5fa'}`,
                  }}
                >
                  <div className="flex flex-wrap items-start gap-3 mb-3">
                    <div className="flex-1">
                      <p className="font-semibold text-white">
                        {FIELD_LABELS[v.field_name] ?? v.field_name.replace(/_/g, ' ')}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <SeverityBadge severity={v.severity} />
                      <ConfidenceBadge confidence={v.confidence} />
                    </div>
                  </div>
                  <p className="text-sm mb-3" style={{ color: 'rgba(226,232,240,0.65)' }}>
                    {v.reason}
                  </p>
                  {v.rule_id && (
                    <p className="text-xs font-mono" style={{ color: 'rgba(212,175,55,0.6)' }}>
                      Rule: {v.rule_id}
                    </p>
                  )}
                  {v.evidence && (
                    <p className="text-xs mt-1 font-mono" style={{ color: 'rgba(226,232,240,0.3)' }}>
                      Evidence: "{v.evidence.slice(0, 100)}"
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'reports' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-xl">
            <button
              className="glass-card p-6 text-left transition-all hover:border-gold group"
              style={{ border: '1px solid rgba(212,175,55,0.2)', cursor: 'pointer' }}
              onClick={() => handleDownload('pdf')}
              disabled={downloading !== null}
            >
              <div className="flex items-center gap-3 mb-3">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center"
                  style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)' }}
                >
                  <FileText className="w-5 h-5" style={{ color: '#fca5a5' }} />
                </div>
                <div>
                  <p className="font-semibold text-white text-sm">Download PDF</p>
                  <p className="text-xs" style={{ color: 'rgba(226,232,240,0.45)' }}>
                    Official inspection report
                  </p>
                </div>
              </div>
              <button className="btn-primary text-xs flex items-center gap-1.5 w-full justify-center">
                {downloading === 'pdf' ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Download className="w-3.5 h-3.5" />
                )}
                {downloading === 'pdf' ? 'Generating...' : 'Download PDF'}
              </button>
            </button>

            <button
              className="glass-card p-6 text-left"
              style={{ border: '1px solid rgba(212,175,55,0.2)', cursor: 'pointer' }}
              onClick={() => handleDownload('docx')}
              disabled={downloading !== null}
            >
              <div className="flex items-center gap-3 mb-3">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center"
                  style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)' }}
                >
                  <FileText className="w-5 h-5" style={{ color: '#93c5fd' }} />
                </div>
                <div>
                  <p className="font-semibold text-white text-sm">Download DOCX</p>
                  <p className="text-xs" style={{ color: 'rgba(226,232,240,0.45)' }}>
                    Editable Word document
                  </p>
                </div>
              </div>
              <button className="btn-primary text-xs flex items-center gap-1.5 w-full justify-center">
                {downloading === 'docx' ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Download className="w-3.5 h-3.5" />
                )}
                {downloading === 'docx' ? 'Generating...' : 'Download DOCX'}
              </button>
            </button>

            <div
              className="sm:col-span-2 rounded-xl p-4 text-xs"
              style={{
                background: 'rgba(245,158,11,0.06)',
                border: '1px solid rgba(245,158,11,0.15)',
                color: 'rgba(252,211,77,0.65)',
              }}
            >
              ⚠️ Reports are generated by an automated system. All findings must be physically
              verified by a qualified Legal Metrology Inspector. Not for enforcement use.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
