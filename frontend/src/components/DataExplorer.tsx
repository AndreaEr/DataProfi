import { useState, useEffect, Fragment } from 'react';
import { getProfile, getOutlierDetails } from '../api/client';
import type { OutlierDetail } from '../api/client';
import type { ColumnProfile } from '../types';

interface Props {
  datasetId: string;
  columns: string[];
}

export default function DataExplorer({ datasetId, columns }: Props) {
  const [profiles, setProfiles] = useState<ColumnProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [outlierData, setOutlierData] = useState<OutlierDetail | null>(null);

  useEffect(() => {
    setLoading(true);
    getProfile(datasetId)
      .then(setProfiles)
      .finally(() => setLoading(false));
  }, [datasetId]);

  useEffect(() => {
    setOutlierData(null);
    if (expandedRow) {
      const profile = profiles.find(p => p.name === expandedRow);
      if (profile && profile.outlier_count > 0) {
        getOutlierDetails(datasetId, expandedRow).then(setOutlierData).catch(() => {});
      }
    }
  }, [expandedRow, datasetId, profiles]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="flex items-center gap-2 text-sm text-brand-600">
          <div className="w-4 h-4 border-2 border-brand-200 border-t-brand-600 rounded-full animate-spin" />
          Loading schema...
        </div>
      </div>
    );
  }

  const issueCount = profiles.reduce((sum, p) => sum + p.quality_issues.length, 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-slate-900">Schema Explorer</h2>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-500">{columns.length} columns</span>
          {issueCount > 0 && (
            <span className="badge bg-rose-50 text-rose-600 border border-rose-100">
              {issueCount} issue{issueCount !== 1 ? 's' : ''} found
            </span>
          )}
        </div>
      </div>

      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/50">
                <th className="px-4 py-3 text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Column</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Type</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Complete</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Unique</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Min</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Max</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Distribution</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {profiles.map((p) => (
                <Fragment key={p.name}>
                  <tr
                    className={`transition-colors cursor-pointer ${
                      expandedRow === p.name ? 'bg-brand-50/50' : 'hover:bg-slate-50'
                    }`}
                    onClick={() => setExpandedRow(expandedRow === p.name ? null : p.name)}
                  >
                    <td className="px-4 py-3 text-sm font-mono text-slate-800 font-medium">{p.name}</td>
                    <td className="px-4 py-3">
                      <span className="badge bg-slate-100 text-slate-600">{p.dtype}</span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`font-medium ${p.completeness >= 95 ? 'text-emerald-600' : 'text-rose-600'}`}>
                        {p.completeness.toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600">{p.unique_count.toLocaleString()}</td>
                    <td className="px-4 py-3 text-sm text-slate-500 truncate max-w-[100px]">
                      {p.min_value || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-500 truncate max-w-[100px]">
                      {p.max_value || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-500">{p.distribution || '-'}</td>
                    <td className="px-4 py-3">
                      {p.quality_issues.length > 0 ? (
                        <span className="badge bg-rose-50 text-rose-600 border border-rose-100">
                          {p.quality_issues.length} issue{p.quality_issues.length > 1 ? 's' : ''}
                        </span>
                      ) : (
                        <span className="badge bg-emerald-50 text-emerald-600 border border-emerald-100">OK</span>
                      )}
                    </td>
                  </tr>
                  {expandedRow === p.name && p.quality_issues.length > 0 && (
                    <tr>
                      <td colSpan={8} className="px-4 py-3 bg-rose-50/50 border-l-2 border-rose-300">
                        <div className="pl-2">
                          <p className="text-xs font-semibold text-rose-700 uppercase tracking-wide mb-2">
                            Quality Issues for "{p.name}"
                          </p>
                          <ul className="space-y-1">
                            {p.quality_issues.map((issue, i) => (
                              <li key={i} className="text-sm text-slate-700 flex items-center gap-2">
                                <span className="w-1.5 h-1.5 bg-rose-400 rounded-full flex-shrink-0" />
                                {issue}
                              </li>
                            ))}
                          </ul>
                          {outlierData && outlierData.rows.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-rose-200">
                              <p className="text-xs font-semibold text-rose-700 uppercase tracking-wide mb-2">
                                Outlier Records
                              </p>
                              {outlierData.context && (
                                <p className="text-xs text-slate-500 mb-2">
                                  Normal range: {outlierData.context.normal_min} to {outlierData.context.normal_max} (mean: {outlierData.context.mean})
                                </p>
                              )}
                              <div className="space-y-1.5">
                                {outlierData.rows.map((row, ri) => (
                                  <div key={ri} className="p-2 rounded border border-rose-100 bg-white">
                                    <div className="flex items-center justify-between mb-0.5">
                                      <span className="text-[11px] text-slate-500">Row {row._row}</span>
                                      <span className="text-xs font-mono font-bold text-rose-600">{row._value}</span>
                                    </div>
                                    {row._reason && (
                                      <p className="text-[11px] text-slate-600">{row._reason}</p>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                  {expandedRow === p.name && p.quality_issues.length === 0 && (
                    <tr>
                      <td colSpan={8} className="px-4 py-3 bg-emerald-50/50 border-l-2 border-emerald-300">
                        <p className="text-sm text-emerald-700 pl-2">No quality issues detected for this column.</p>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

