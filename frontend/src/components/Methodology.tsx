import { useState, useEffect } from 'react';
import { getMethodology } from '../api/client';

interface Dimension {
  name: string;
  weight: number;
  iso_25012_mapping: string;
  dama_mapping: string;
  definition: string;
  formula: string;
  thresholds?: Record<string, string>;
  checks_performed?: string[];
  issues_detected?: string[];
  note?: string;
}

interface MethodologyData {
  framework: string;
  version: string;
  description: string;
  dimensions: Dimension[];
  overall_score: {
    formula: string;
    range: string;
    interpretation: Record<string, string>;
  };
  outlier_detection: {
    method: string;
    formula: string;
    alternative: string;
    reference: string;
  };
  references: string[];
}

export default function Methodology() {
  const [data, setData] = useState<MethodologyData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getMethodology()
      .then((d) => setData(d as unknown as MethodologyData))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="flex items-center gap-2 text-sm text-brand-600">
          <div className="w-4 h-4 border-2 border-brand-200 border-t-brand-600 rounded-full animate-spin" />
          Loading methodology...
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center gap-2 mb-2">
          <span className="badge bg-brand-50 text-brand-700 border border-brand-100">{data.framework}</span>
          <span className="badge bg-slate-100 text-slate-600">v{data.version}</span>
        </div>
        <p className="text-sm text-slate-600 leading-relaxed">{data.description}</p>
      </div>

      <div className="card">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">
          Quality Dimensions
        </p>
        <div className="space-y-4">
          {data.dimensions.map((dim) => (
            <div key={dim.name} className="p-4 rounded-lg border border-slate-200 bg-slate-50/50">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-bold text-slate-800">{dim.name}</h3>
                <div className="flex items-center gap-2">
                  <span className="badge bg-brand-50 text-brand-700">Weight: {(dim.weight * 100).toFixed(0)}%</span>
                  <span className="badge bg-slate-100 text-slate-600 text-[10px]">ISO: {dim.iso_25012_mapping}</span>
                </div>
              </div>
              <p className="text-sm text-slate-600 mb-3">{dim.definition}</p>
              <div className="text-xs font-mono bg-white rounded px-3 py-2 border border-slate-200 text-slate-700 mb-2">
                {dim.formula}
              </div>
              {dim.checks_performed && (
                <div className="mt-2">
                  <p className="text-[11px] font-semibold text-slate-500 mb-1">Checks:</p>
                  <ul className="space-y-0.5">
                    {dim.checks_performed.map((check, i) => (
                      <li key={i} className="text-xs text-slate-600 flex items-center gap-1.5">
                        <span className="w-1 h-1 bg-slate-400 rounded-full flex-shrink-0" />
                        {check}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {dim.thresholds && (
                <div className="mt-2 grid grid-cols-4 gap-2">
                  {Object.entries(dim.thresholds).map(([level, threshold]) => (
                    <div key={level} className="text-center p-1.5 rounded bg-white border border-slate-200">
                      <p className="text-[10px] text-slate-400 capitalize">{level}</p>
                      <p className="text-xs font-semibold text-slate-700">{threshold}</p>
                    </div>
                  ))}
                </div>
              )}
              {dim.note && (
                <p className="text-xs text-slate-400 mt-2 italic">{dim.note}</p>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
            Overall Score
          </p>
          <div className="text-xs font-mono bg-slate-50 rounded px-3 py-2 border border-slate-200 text-slate-700 mb-3">
            {data.overall_score.formula}
          </div>
          <div className="space-y-1.5">
            {Object.entries(data.overall_score.interpretation).map(([range, meaning]) => (
              <div key={range} className="flex items-center justify-between text-xs">
                <span className="font-mono text-slate-600">{range.replace('_', ' ')}</span>
                <span className="text-slate-500">{meaning}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
            Outlier Detection
          </p>
          <p className="text-sm font-medium text-slate-700 mb-1">{data.outlier_detection.method}</p>
          <div className="text-xs font-mono bg-slate-50 rounded px-3 py-2 border border-slate-200 text-slate-700 mb-2">
            {data.outlier_detection.formula}
          </div>
          <p className="text-xs text-slate-500">{data.outlier_detection.alternative}</p>
          <p className="text-[10px] text-slate-400 mt-2 italic">{data.outlier_detection.reference}</p>
        </div>
      </div>

      <div className="card">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
          References
        </p>
        <ol className="list-decimal list-inside space-y-1.5">
          {data.references.map((ref, i) => (
            <li key={i} className="text-xs text-slate-600">{ref}</li>
          ))}
        </ol>
      </div>
    </div>
  );
}
