import { CheckCircle, AlertTriangle, Eye } from 'lucide-react';
import type { ComplianceStatus } from '../types';

export function StatusBadge({ status }: { status: ComplianceStatus }) {
  if (status === 'COMPLIANT') {
    return (
      <span className="badge-compliant">
        <CheckCircle className="w-3 h-3" />
        COMPLIANT
      </span>
    );
  }
  if (status === 'NON-COMPLIANT') {
    return (
      <span className="badge-violation">
        <AlertTriangle className="w-3 h-3" />
        NON-COMPLIANT
      </span>
    );
  }
  if (status === 'NOT APPLICABLE') {
    return (
      <span className="badge-review" style={{ background: 'rgba(255,255,255,0.1)', color: '#d1d5db', border: '1px solid rgba(255,255,255,0.2)' }}>
        <Eye className="w-3 h-3" />
        NOT APPLICABLE
      </span>
    );
  }
  if (status === 'NOT VERIFIABLE') {
    return (
      <span className="badge-review" style={{ background: 'rgba(239,68,68,0.05)', color: '#f87171', border: '1px solid rgba(239,68,68,0.2)' }}>
        <AlertTriangle className="w-3 h-3" />
        NOT VERIFIABLE
      </span>
    );
  }
  return (
    <span className="badge-review">
      <Eye className="w-3 h-3" />
      NEEDS REVIEW
    </span>
  );
}

export function ConfidenceBadge({ confidence }: { confidence: string }) {
  const colors: Record<string, { bg: string; text: string; border: string }> = {
    HIGH: {
      bg: 'rgba(16,185,129,0.1)',
      text: '#6ee7b7',
      border: 'rgba(16,185,129,0.25)',
    },
    MEDIUM: {
      bg: 'rgba(245,158,11,0.1)',
      text: '#fcd34d',
      border: 'rgba(245,158,11,0.25)',
    },
    LOW: {
      bg: 'rgba(239,68,68,0.1)',
      text: '#fca5a5',
      border: 'rgba(239,68,68,0.25)',
    },
  };
  const c = colors[confidence] ?? colors.LOW;
  return (
    <span
      className="inline-block px-2 py-0.5 rounded text-xs font-semibold"
      style={{ background: c.bg, color: c.text, border: `1px solid ${c.border}` }}
    >
      {confidence}
    </span>
  );
}

export function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, { bg: string; text: string; border: string }> = {
    HIGH: { bg: 'rgba(239,68,68,0.15)', text: '#fca5a5', border: 'rgba(239,68,68,0.3)' },
    MEDIUM: {
      bg: 'rgba(245,158,11,0.15)',
      text: '#fcd34d',
      border: 'rgba(245,158,11,0.3)',
    },
    LOW: {
      bg: 'rgba(59,130,246,0.15)',
      text: '#93c5fd',
      border: 'rgba(59,130,246,0.3)',
    },
  };
  const c = colors[severity] ?? colors.MEDIUM;
  return (
    <span
      className="inline-block px-2 py-0.5 rounded text-xs font-semibold"
      style={{ background: c.bg, color: c.text, border: `1px solid ${c.border}` }}
    >
      {severity}
    </span>
  );
}
