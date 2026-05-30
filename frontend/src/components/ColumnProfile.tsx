import { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { getEnhancedProfile, getOutlierDetails } from '../api/client';
import type { OutlierDetail } from '../api/client';
import type { EnhancedColumnProfile } from '../types';

interface Props {
  datasetId: string;
}

const ROLE_BADGE: Record<string, { bg: string; text: string; label: string }> = {
  id: { bg: 'bg-slate-100', text: 'text-slate-700', label: 'ID' },
  category: { bg: 'bg-violet-50', text: 'text-violet-700', label: 'Category' },
  measure: { bg: 'bg-brand-50', text: 'text-brand-700', label: 'Measure' },
  datetime: { bg: 'bg-amber-50', text: 'text-amber-700', label: 'DateTime' },
  free_text: { bg: 'bg-emerald-50', text: 'text-emerald-700', label: 'Text' },
  boolean: { bg: 'bg-pink-50', text: 'text-pink-700', label: 'Boolean' },
};

export default function ColumnProfileView({ datasetId }: Props) {
  const [profiles, setProfiles] = useState<EnhancedColumnProfile[]>([]);
  const [selected, setSelected] = useState<EnhancedColumnProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [outlierData, setOutlierData] = useState<OutlierDetail | null>(null);

  useEffect(() => {
    setLoading(true);
    getEnhancedProfile(datasetId)
      .then((data) => {
        setProfiles(data);
        if (data.length > 0) setSelected(data[0]);
      })
      .finally(() => setLoading(false));
  }, [datasetId]);

  useEffect(() => {
    setOutlierData(null);
    if (selected && selected.outlier_count > 0) {
      getOutlierDetails(datasetId, selected.name).then(setOutlierData).catch(() => {});
    }
  }, [selected, datasetId]);

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

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Column list */}
        <div className="card p-4">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
            Columns ({profiles.length})
          </p>
          <div className="space-y-0.5 max-h-[500px] overflow-y-auto">
            {profiles.map((p) => {
              const badge = ROLE_BADGE[p.role] || ROLE_BADGE.measure;
              return (
                <button
                  key={p.name}
                  onClick={() => setSelected(p)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg transition-colors ${
                    selected?.name === p.name
                      ? 'bg-brand-50 border border-brand-100'
                      : 'hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className={`text-sm truncate ${selected?.name === p.name ? 'font-medium text-brand-700' : 'text-slate-700'}`}>
                      {p.name}
                    </span>
                    <span className={`badge text-[10px] ${badge.bg} ${badge.text} flex-shrink-0`}>
                      {badge.label}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Detail pane */}
        {selected && (
          <div className="md:col-span-3 space-y-4">
            {/* Header + insight */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                  <h3 className="text-base font-bold text-slate-900">{selected.name}</h3>
                  <span className={`badge ${ROLE_BADGE[selected.role]?.bg || ''} ${ROLE_BADGE[selected.role]?.text || ''} border border-slate-200`}>
                    {ROLE_BADGE[selected.role]?.label || selected.role}
                  </span>
                  <span className="badge bg-slate-100 text-slate-600">{selected.dtype}</span>
                </div>
                <span className={`text-sm font-semibold ${selected.completeness >= 95 ? 'text-emerald-600' : 'text-amber-600'}`}>
                  {selected.completeness.toFixed(1)}% complete
                </span>
              </div>

              {/* Insight card */}
              <div className="p-3.5 rounded-lg bg-brand-50/50 border border-brand-100">
                <p className="text-sm text-brand-800">{selected.insight}</p>
              </div>
            </div>

            {/* Role-specific details */}
            {selected.role === 'category' && selected.category_stats && (
              <div className="card">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">
                  Value Distribution
                </p>
                {selected.category_stats.is_skewed && (
                  <p className="text-xs text-amber-600 mb-3 font-medium">
                    Skewed: dominant value accounts for {selected.category_stats.dominant_value_pct}% of data
                  </p>
                )}
                <ResponsiveContainer width="100%" height={Math.min(200, selected.category_stats.top_values.length * 32)}>
                  <BarChart data={selected.category_stats.top_values} layout="vertical">
                    <XAxis type="number" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                    <YAxis
                      type="category"
                      dataKey="value"
                      tick={{ fontSize: 11, fill: '#64748b' }}
                      width={100}
                    />
                    <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }} />
                    <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {selected.role === 'measure' && selected.numeric_insight && (
              <div className="card">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">
                  Distribution Analysis
                </p>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
                  <Stat label="Median" value={selected.numeric_insight.median.toLocaleString()} />
                  <Stat label="Range" value={selected.numeric_insight.range_value.toLocaleString()} />
                  <Stat label="Shape" value={selected.numeric_insight.distribution_shape.replace('_', ' ')} />
                  <Stat label="P25" value={selected.numeric_insight.percentile_25.toLocaleString()} />
                  <Stat label="P75" value={selected.numeric_insight.percentile_75.toLocaleString()} />
                  <Stat label="Outliers" value={String(selected.outlier_count)} />
                </div>
                {selected.numeric_insight.interpretation && (
                  <p className="text-sm text-slate-600 p-3 bg-slate-50 rounded-lg border border-slate-100">
                    {selected.numeric_insight.interpretation}
                  </p>
                )}
              </div>
            )}

            {selected.role === 'datetime' && selected.datetime_insight && (
              <div className="card">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">
                  Temporal Details
                </p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <Stat label="Start" value={selected.datetime_insight.date_range_start} />
                  <Stat label="End" value={selected.datetime_insight.date_range_end} />
                  <Stat label="Frequency" value={selected.datetime_insight.frequency || 'unknown'} />
                  <Stat label="Gaps" value={String(selected.datetime_insight.gap_count)} />
                </div>
              </div>
            )}

            {selected.role === 'boolean' && selected.category_stats && (
              <div className="card">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">
                  Value Breakdown
                </p>
                <div className="grid grid-cols-2 gap-3">
                  {selected.category_stats.top_values.map((v) => (
                    <Stat key={v.value} label={String(v.value)} value={`${v.count} records`} />
                  ))}
                </div>
              </div>
            )}

            {/* General stats for all roles */}
            <div className="card">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">
                Column Statistics
              </p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <Stat label="Total rows" value={selected.total_count.toLocaleString()} />
                <Stat label="Null count" value={selected.null_count.toLocaleString()} />
                <Stat label="Unique values" value={selected.unique_count.toLocaleString()} />
                <Stat label="Unique ratio" value={`${(selected.unique_ratio * 100).toFixed(1)}%`} />
                {selected.mean !== null && <Stat label="Mean" value={selected.mean.toFixed(2)} />}
                {selected.std !== null && <Stat label="Std dev" value={selected.std.toFixed(2)} />}
                {selected.min_value && <Stat label="Min" value={selected.min_value} />}
                {selected.max_value && <Stat label="Max" value={selected.max_value} />}
              </div>
            </div>

            {/* Anomalies */}
            {selected.anomaly_context.length > 0 && (
              <div className="card border-amber-200 bg-amber-50/30">
                <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-3">
                  Anomalies ({selected.anomaly_context.length})
                </p>
                <ul className="space-y-2">
                  {selected.anomaly_context.map((ctx, i) => (
                    <li key={i} className="text-sm text-slate-700 flex items-start gap-2">
                      <span className="w-1.5 h-1.5 bg-amber-400 rounded-full flex-shrink-0 mt-1.5" />
                      {ctx}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Outlier rows detail */}
            {outlierData && outlierData.rows.length > 0 && (
              <div className="card">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
                  Outlier Records ({outlierData.outlier_count} rows)
                </p>
                {outlierData.context && (
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 mb-4 text-xs text-slate-600">
                    <p className="font-medium text-slate-700 mb-1">Normal range for this column:</p>
                    <p>
                      Values are expected between <span className="font-mono font-semibold">{outlierData.context.normal_min}</span> and <span className="font-mono font-semibold">{outlierData.context.normal_max}</span> (mean: {outlierData.context.mean}).
                    </p>
                    <p className="text-slate-400 mt-1">Method: {outlierData.context.method}</p>
                  </div>
                )}
                <div className="space-y-2">
                  {outlierData.rows.map((row, i) => (
                    <div key={i} className="p-3 rounded-lg border border-rose-100 bg-rose-50/30">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-slate-500">Row {row._row}</span>
                        <span className="text-sm font-mono font-bold text-rose-600">{row._value}</span>
                      </div>
                      <p className="text-xs text-slate-600">{row._reason}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
      <p className="text-[11px] text-slate-400 mb-0.5 font-medium">{label}</p>
      <p className="text-sm font-semibold text-slate-800 truncate">{value}</p>
    </div>
  );
}
