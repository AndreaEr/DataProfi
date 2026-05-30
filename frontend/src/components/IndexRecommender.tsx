import { useState, useEffect } from 'react';
import { getIndexRecommendations } from '../api/client';
import type { IndexRecommendation } from '../types';

interface Props {
  datasetId: string;
}

export default function IndexRecommender({ datasetId }: Props) {
  const [recommendations, setRecommendations] = useState<IndexRecommendation[]>([]);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState<number | null>(null);

  useEffect(() => {
    setLoading(true);
    getIndexRecommendations(datasetId)
      .then(setRecommendations)
      .finally(() => setLoading(false));
  }, [datasetId]);

  const copySQL = (sql: string, idx: number) => {
    navigator.clipboard.writeText(sql);
    setCopied(idx);
    setTimeout(() => setCopied(null), 2000);
  };

  const priorityStyle = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-rose-50 text-rose-700 border border-rose-100';
      case 'medium': return 'bg-amber-50 text-amber-700 border border-amber-100';
      default: return 'bg-slate-50 text-slate-600 border border-slate-200';
    }
  };

  const indexTypeStyle = (type: string) => {
    switch (type) {
      case 'btree': return 'bg-brand-50 text-brand-700 border border-brand-100';
      case 'gin': return 'bg-indigo-50 text-indigo-700 border border-indigo-100';
      case 'brin': return 'bg-emerald-50 text-emerald-700 border border-emerald-100';
      case 'gist': return 'bg-amber-50 text-amber-700 border border-amber-100';
      default: return 'bg-slate-100 text-slate-600 border border-slate-200';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="flex items-center gap-2 text-sm text-brand-600">
          <div className="w-4 h-4 border-2 border-brand-200 border-t-brand-600 rounded-full animate-spin" />
          Analyzing columns...
        </div>
      </div>
    );
  }

  if (recommendations.length === 0) {
    return (
      <div className="card text-center py-12">
        <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3">
          <span className="text-slate-400 text-lg">--</span>
        </div>
        <p className="text-slate-600 font-medium">No index recommendations</p>
        <p className="text-sm text-slate-400 mt-1">
          All columns have low cardinality or the table is too small to benefit.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-slate-900">
          {recommendations.length} Recommendation{recommendations.length !== 1 ? 's' : ''}
        </h2>
        <button
          onClick={() => {
            const allSQL = recommendations.map((r) => r.sql).join('\n');
            navigator.clipboard.writeText(allSQL);
          }}
          className="btn-secondary text-xs"
        >
          Copy All SQL
        </button>
      </div>

      <div className="space-y-2">
        {recommendations.map((rec, idx) => (
          <div key={idx} className="card p-0 overflow-hidden">
            <div
              className="flex items-center justify-between px-5 py-4 cursor-pointer hover:bg-slate-50 transition-colors"
              onClick={() => setExpandedIdx(expandedIdx === idx ? null : idx)}
            >
              <div className="flex items-center gap-2.5">
                <span className={`badge ${priorityStyle(rec.priority)}`}>
                  {rec.priority}
                </span>
                <span className={`badge ${indexTypeStyle(rec.index_type)}`}>
                  {rec.index_type}
                </span>
                <span className="font-mono text-sm text-slate-800 font-medium">{rec.column}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-slate-400 hidden md:inline">{rec.estimated_impact}</span>
                <span className={`text-brand-500 text-xs transition-transform ${expandedIdx === idx ? 'rotate-90' : ''}`}>{'>'}</span>
              </div>
            </div>

            {expandedIdx === idx && (
              <div className="px-5 pb-5 border-t border-slate-100 pt-4">
                <p className="text-sm text-slate-600 mb-4">{rec.reason}</p>
                <div className="bg-slate-900 rounded-lg p-4 mb-4">
                  <div className="flex justify-between items-start">
                    <code className="text-sm text-brand-300 font-mono">{rec.sql}</code>
                    <button
                      onClick={(e) => { e.stopPropagation(); copySQL(rec.sql, idx); }}
                      className="text-xs text-slate-500 hover:text-white ml-4 shrink-0 transition-colors"
                    >
                      {copied === idx ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                </div>
                <details className="text-sm">
                  <summary className="text-brand-600 cursor-pointer hover:text-brand-800 font-medium">
                    Why this index helps
                  </summary>
                  <pre className="mt-3 text-xs text-slate-600 whitespace-pre-wrap bg-slate-50 rounded-lg p-4 border border-slate-200">
                    {rec.explanation}
                  </pre>
                </details>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
