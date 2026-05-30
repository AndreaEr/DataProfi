import { useState, useEffect } from 'react';
import { cleanDataset, getDataPreview, getDownloadUrl } from '../api/client';
import type { CleanResponse } from '../types';
import type { DataPreview } from '../api/client';

interface Props {
  datasetId: string;
}

export default function BeforeAfter({ datasetId }: Props) {
  const [result, setResult] = useState<CleanResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [beforePreview, setBeforePreview] = useState<DataPreview | null>(null);
  const [afterPreview, setAfterPreview] = useState<DataPreview | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  useEffect(() => {
    getDataPreview(datasetId, 8).then(setBeforePreview).catch(() => {});
  }, [datasetId]);

  const presets = [
    {
      name: 'Auto Clean',
      description: 'Type coercion, dedup, median imputation, outlier clipping',
      steps: [
        { step_type: 'types' },
        { step_type: 'duplicates', method: 'exact' },
        { step_type: 'missing', strategy: 'median' },
        { step_type: 'outliers', method: 'iqr', action: 'clip' },
      ],
    },
    {
      name: 'Conservative',
      description: 'Remove exact duplicates and flag outliers only',
      steps: [
        { step_type: 'duplicates', method: 'exact' },
        { step_type: 'outliers', method: 'iqr', action: 'flag' },
      ],
    },
    {
      name: 'Aggressive',
      description: 'Drop missing rows, remove outliers, strict dedup',
      steps: [
        { step_type: 'types' },
        { step_type: 'duplicates', method: 'exact' },
        { step_type: 'missing', strategy: 'drop' },
        { step_type: 'outliers', method: 'zscore', action: 'remove', threshold: 3 },
      ],
    },
  ];

  const runPreset = async (steps: Array<{ step_type: string; [key: string]: unknown }>) => {
    setLoading(true);
    setError('');
    try {
      const res = await cleanDataset(datasetId, steps);
      setResult(res);
      const after = await getDataPreview(datasetId, 8);
      setAfterPreview(after);
      setShowPreview(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Cleaning failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    const url = getDownloadUrl(datasetId);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cleaned_${datasetId}.csv`;
    a.click();
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">
          Cleaning Presets
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {presets.map((preset) => (
            <button
              key={preset.name}
              onClick={() => runPreset(preset.steps)}
              disabled={loading}
              className="text-left p-5 rounded-xl border border-slate-200 hover:border-brand-300 hover:bg-brand-50/30 transition-all disabled:opacity-50 group"
            >
              <p className="font-semibold text-sm text-slate-800 group-hover:text-brand-700 mb-1">{preset.name}</p>
              <p className="text-xs text-slate-400">{preset.description}</p>
            </button>
          ))}
        </div>
        {loading && (
          <div className="mt-4 flex items-center gap-2 text-sm text-brand-600">
            <div className="w-3 h-3 border-2 border-brand-200 border-t-brand-600 rounded-full animate-spin" />
            Running pipeline...
          </div>
        )}
        {error && (
          <div className="mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200">
            <p className="text-sm text-rose-700">{error}</p>
          </div>
        )}
      </div>

      {result && (
        <>
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-800">Results</h3>
            <div className="flex items-center gap-2">
              <button onClick={() => setShowPreview(!showPreview)} className="btn-secondary text-xs">
                {showPreview ? 'Hide Preview' : 'Show Preview'}
              </button>
              <button onClick={handleDownload} className="btn-primary text-xs">
                Download Cleaned CSV
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="stat-card text-center">
              <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold mb-3">Quality Score</p>
              <div className="flex items-center justify-center gap-3">
                <span className="text-2xl text-slate-400">{result.score_before.toFixed(0)}</span>
                <span className="text-slate-300 text-sm">to</span>
                <span className="text-2xl font-bold text-emerald-600">{result.score_after.toFixed(0)}</span>
              </div>
              <p className="text-xs text-emerald-600 font-medium mt-2">
                +{(result.score_after - result.score_before).toFixed(1)} points
              </p>
            </div>

            <div className="stat-card text-center">
              <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold mb-3">Rows</p>
              <div className="flex items-center justify-center gap-3">
                <span className="text-2xl text-slate-400">{result.rows_before.toLocaleString()}</span>
                <span className="text-slate-300 text-sm">to</span>
                <span className="text-2xl font-bold text-slate-800">{result.rows_after.toLocaleString()}</span>
              </div>
              {result.rows_before !== result.rows_after && (
                <p className="text-xs text-slate-400 mt-2">
                  {result.rows_before - result.rows_after} removed
                </p>
              )}
            </div>

            <div className="stat-card text-center">
              <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold mb-3">Actions Taken</p>
              <p className="text-4xl font-bold text-brand-600">{result.actions.length}</p>
            </div>
          </div>

          {showPreview && beforePreview && afterPreview && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="card p-4">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
                  Before ({beforePreview.total_rows} rows)
                </p>
                <PreviewTable columns={beforePreview.columns} rows={beforePreview.rows} />
              </div>
              <div className="card p-4 border-emerald-200">
                <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wide mb-3">
                  After ({afterPreview.total_rows} rows)
                </p>
                <PreviewTable columns={afterPreview.columns} rows={afterPreview.rows} />
              </div>
            </div>
          )}

          <div className="card">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">
              Changes Applied
            </p>
            <div className="space-y-2">
              {result.actions.map((action, i) => (
                <div key={i} className="flex items-start gap-3 py-3 border-b border-slate-100 last:border-0">
                  <span className="mt-1.5 w-2 h-2 bg-brand-400 rounded-full flex-shrink-0" />
                  <div>
                    <p className="text-sm text-slate-700">{action.description}</p>
                    <div className="flex flex-wrap gap-2 mt-1.5">
                      <span className="badge bg-brand-50 text-brand-700 font-mono border border-brand-100">
                        {action.column}
                      </span>
                      <span className="badge bg-indigo-50 text-indigo-600 border border-indigo-100">
                        {action.strategy}
                      </span>
                      <span className="text-xs text-slate-400">
                        {action.rows_affected} rows affected
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function PreviewTable({ columns, rows }: { columns: string[]; rows: string[][] }) {
  return (
    <div className="overflow-x-auto max-h-64">
      <table className="min-w-full text-[11px]">
        <thead>
          <tr className="border-b border-slate-200">
            {columns.slice(0, 6).map((col) => (
              <th key={col} className="px-2 py-1.5 text-left font-semibold text-slate-500 whitespace-nowrap">
                {col.length > 12 ? col.slice(0, 12) + '..' : col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-50">
          {rows.map((row, i) => (
            <tr key={i}>
              {row.slice(0, 6).map((val, j) => (
                <td key={j} className="px-2 py-1 text-slate-600 truncate max-w-[100px]">
                  {val || '-'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
