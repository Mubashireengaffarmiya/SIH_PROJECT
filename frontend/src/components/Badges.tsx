import { CheckCircle, AlertTriangle, Eye } from 'lucide-react';
import type { ComplianceStatus } from '../types';

export function StatusBadge({ status }: { status: ComplianceStatus }) {
  if (status === 'VERIFIED_COMPLIANT') {
    return (
      <span className="badge-compliant">
        <CheckCircle className="w-3 h-3" />
        COMPLIANT
      </span>
    );
  }
  if (status === 'POTENTIAL_VIOLATION') {
    return (
      <span className="badge-violation">
        <AlertTriangle className="w-3 h-3" />
        VIOLATION
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
