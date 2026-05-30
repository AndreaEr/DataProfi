import { useState, useEffect } from 'react';
import { getCorrelations } from '../api/client';
import type { CorrelationReport } from '../types';

interface Props {
  datasetId: string;
}

function corrColor(value: number): string {
  const abs = Math.abs(value);
  if (abs > 0.8) return value > 0 ? 'bg-brand-600 text-white' : 'bg-rose-600 text-white';
  if (abs > 0.5) return value > 0 ? 'bg-brand-200 text-brand-900' : 'bg-rose-200 text-rose-900';
  if (abs > 0.3) return value > 0 ? 'bg-brand-50 text-brand-700' : 'bg-rose-50 text-rose-700';
  return 'bg-slate-50 text-slate-500';
}

export default function CorrelationView({ datasetId }: Props) {
  const [report, setReport] = useState<CorrelationReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getCorrelations(datasetId)
      .then(setReport)
      .finally(() => setLoading(false));
  }, [datasetId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="flex items-center gap-2 text-sm text-brand-600">
          <div className="w-4 h-4 border-2 border-brand-200 border-t-brand-600 rounded-full animate-spin" />
          Computing correlations...
        </div>
      </div>
    );
  }

  if (!report) return null;

  const matrixCols = Object.keys(report.correlation_matrix);
  const hasMatrix = matrixCols.length >= 2 && matrixCols.length <= 15;
  const hasNumeric = report.numeric_correlations.length > 0;
  const hasCategorical = report.categorical_associations.length > 0;
  const hasDeps = report.functional_dependencies.length > 0;
  const hasRedundant = report.redundant_columns.length > 0;

  if (!hasNumeric && !hasCategorical && !hasDeps) {
    return (
      <div className="card text-center py-12">
        <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3">
          <span className="text-slate-400 text-sm font-medium">--</span>
        </div>
        <p className="text-slate-600 font-medium">No notable correlations found</p>
        <p className="text-sm text-slate-400 mt-1">
          Columns appear to be independent of each other.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {hasRedundant && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200">
          <p className="text-sm font-semibold text-amber-800 mb-2">Redundant columns detected</p>
          <div className="space-y-1.5">
            {report.redundant_columns.map(([a, b, corr], i) => (
              <p key={i} className="text-sm text-amber-700">
                <span className="font-mono font-medium">{a}</span> and{' '}
                <span className="font-mono font-medium">{b}</span> are nearly identical (r={corr})
                - consider dropping one.
              </p>
            ))}
          </div>
        </div>
      )}

      {hasMatrix && (
        <div className="card">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">
            Correlation Matrix
          </p>
          <div className="overflow-x-auto">
            <table className="text-xs">
              <thead>
                <tr>
                  <th className="px-2 py-1" />
                  {matrixCols.map((col) => (
                    <th key={col} className="px-2 py-1 font-mono text-slate-500 font-medium text-center whitespace-nowrap">
                      {col.length > 10 ? col.slice(0, 10) + '..' : col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {matrixCols.map((rowCol) => (
                  <tr key={rowCol}>
                    <td className="px-2 py-1 font-mono text-slate-600 font-medium whitespace-nowrap">
                      {rowCol.length > 10 ? rowCol.slice(0, 10) + '..' : rowCol}
                    </td>
                    {matrixCols.map((colCol) => {
                      const val = report.correlation_matrix[rowCol]?.[colCol] ?? 0;
                      return (
                        <td key={colCol} className="px-1 py-1 text-center">
                          <span className={`inline-block w-10 px-1 py-0.5 rounded text-[10px] font-medium ${corrColor(val)}`}>
                            {val.toFixed(2)}
                          </span>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {hasNumeric && (
        <div className="card">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">
            Notable Numeric Correlations ({report.numeric_correlations.length})
          </p>
          <div className="space-y-2">
            {report.numeric_correlations.slice(0, 10).map((pair, i) => (
              <div key={i} className="flex items-center gap-3 py-2 border-b border-slate-100 last:border-0">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 text-sm">
                    <span className="font-mono font-medium text-slate-800">{pair.column_a}</span>
                    <span className="text-slate-300">/</span>
                    <span className="font-mono font-medium text-slate-800">{pair.column_b}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-24 bg-slate-100 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full ${pair.correlation > 0 ? 'bg-brand-500' : 'bg-rose-500'}`}
                      style={{ width: `${Math.abs(pair.correlation) * 100}%` }}
                    />
                  </div>
                  <span className={`text-xs font-semibold w-12 text-right ${
                    Math.abs(pair.correlation) > 0.7 ? 'text-brand-700' : 'text-slate-600'
                  }`}>
                    {pair.correlation.toFixed(3)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {hasCategorical && (
        <div className="card">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">
            Categorical Associations (Cramer's V)
          </p>
          <div className="space-y-2">
            {report.categorical_associations.slice(0, 10).map((pair, i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
                <div className="flex items-center gap-1.5 text-sm">
                  <span className="font-mono font-medium text-slate-800">{pair.column_a}</span>
                  <span className="text-slate-300">/</span>
                  <span className="font-mono font-medium text-slate-800">{pair.column_b}</span>
                </div>
                <span className="badge bg-indigo-50 text-indigo-700 border border-indigo-100">
                  V = {pair.correlation.toFixed(3)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {hasDeps && (
        <div className="card">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">
            Functional Dependencies
          </p>
          <div className="space-y-2">
            {report.functional_dependencies.slice(0, 10).map((dep, i) => (
              <div key={i} className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                <p className="text-sm text-slate-700">
                  <span className="font-mono font-semibold text-slate-800">{dep.determinant}</span>
                  {' determines '}
                  <span className="font-mono font-semibold text-slate-800">{dep.dependent}</span>
                </p>
                <p className="text-xs text-slate-400 mt-0.5">
                  Confidence: {(dep.confidence * 100).toFixed(1)}%
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
