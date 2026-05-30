import { useState, useEffect } from 'react';
import { Check, X } from 'lucide-react';
import { getMLReadiness } from '../api/client';
import type { MLReadiness } from '../types';

interface Props {
  datasetId: string;
}

export default function MLReadinessView({ datasetId }: Props) {
  const [readiness, setReadiness] = useState<MLReadiness | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getMLReadiness(datasetId)
      .then(setReadiness)
      .finally(() => setLoading(false));
  }, [datasetId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="flex items-center gap-2 text-sm text-brand-600">
          <div className="w-4 h-4 border-2 border-brand-200 border-t-brand-600 rounded-full animate-spin" />
          Checking ML readiness...
        </div>
      </div>
    );
  }
  if (!readiness) return null;

  const checkStyle = (severity: string, passed: boolean) => {
    if (passed) return 'border-emerald-200 bg-emerald-50/50';
    switch (severity) {
      case 'critical': return 'border-rose-200 bg-rose-50/50';
      case 'warning': return 'border-amber-200 bg-amber-50/50';
      default: return 'border-slate-200 bg-slate-50';
    }
  };

  const iconStyle = (severity: string, passed: boolean) => {
    if (passed) return 'text-emerald-600 bg-emerald-100';
    switch (severity) {
      case 'critical': return 'text-rose-600 bg-rose-100';
      case 'warning': return 'text-amber-600 bg-amber-100';
      default: return 'text-slate-500 bg-slate-100';
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="stat-card text-center">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
            Readiness Score
          </p>
          <p className={`text-5xl font-bold ${readiness.overall_ready ? 'text-emerald-600' : 'text-amber-600'}`}>
            {readiness.score.toFixed(0)}%
          </p>
          <p className="text-sm mt-2 text-slate-500">
            {readiness.overall_ready ? 'Ready for ML training' : 'Issues to resolve first'}
          </p>
        </div>

        <div className="stat-card">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">
            Check Summary
          </p>
          <div className="flex gap-8">
            <div>
              <p className="text-3xl font-bold text-emerald-600">
                {readiness.checks.filter((c) => c.passed).length}
              </p>
              <p className="text-xs text-slate-400 mt-0.5">Passed</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-rose-600">
                {readiness.checks.filter((c) => !c.passed && c.severity === 'critical').length}
              </p>
              <p className="text-xs text-slate-400 mt-0.5">Critical</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-amber-600">
                {readiness.checks.filter((c) => !c.passed && c.severity === 'warning').length}
              </p>
              <p className="text-xs text-slate-400 mt-0.5">Warnings</p>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-2">
        {readiness.checks.map((check, i) => (
          <div
            key={i}
            className={`rounded-xl border p-4 ${checkStyle(check.severity, check.passed)}`}
          >
            <div className="flex items-start gap-3">
              <span className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${iconStyle(check.severity, check.passed)}`}>
                {check.passed ? <Check size={14} /> : <X size={14} />}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-slate-800">{check.name}</span>
                  <span className={`badge ${
                    check.passed ? 'bg-emerald-100 text-emerald-700' :
                    check.severity === 'critical' ? 'bg-rose-100 text-rose-700' :
                    'bg-amber-100 text-amber-700'
                  }`}>
                    {check.severity}
                  </span>
                </div>
                <p className="text-sm text-slate-600 mt-0.5">{check.message}</p>
                {check.suggestion && (
                  <p className="text-xs text-brand-600 mt-1.5 font-medium">{check.suggestion}</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {readiness.recommended_next_steps.length > 0 && (
        <div className="card">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
            Recommended Next Steps
          </p>
          <ol className="list-decimal list-inside space-y-2">
            {readiness.recommended_next_steps.map((step, i) => (
              <li key={i} className="text-sm text-slate-600">{step}</li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
