import { useState, useEffect } from 'react';
import { getTimeseriesProfile } from '../api/client';
import type { TimeseriesReport } from '../types';

interface Props {
  datasetId: string;
}

export default function TimeseriesView({ datasetId }: Props) {
  const [report, setReport] = useState<TimeseriesReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedCol, setExpandedCol] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    getTimeseriesProfile(datasetId)
      .then(setReport)
      .finally(() => setLoading(false));
  }, [datasetId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="flex items-center gap-2 text-sm text-brand-600">
          <div className="w-4 h-4 border-2 border-brand-200 border-t-brand-600 rounded-full animate-spin" />
          Analyzing temporal patterns...
        </div>
      </div>
    );
  }

  if (!report || report.profiles.length === 0) {
    return (
      <div className="card text-center py-12">
        <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3">
          <span className="text-slate-400 text-sm font-medium">--</span>
        </div>
        <p className="text-slate-600 font-medium">No temporal columns detected</p>
        <p className="text-sm text-slate-400 mt-1">
          This dataset does not contain datetime columns for time-series analysis.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-slate-900">Temporal Analysis</h2>
        <span className="text-sm text-slate-500">
          {report.datetime_columns.length} temporal column{report.datetime_columns.length !== 1 ? 's' : ''} detected
        </span>
      </div>

      <div className="space-y-3">
        {report.profiles.map((profile) => (
          <div key={profile.column} className="card p-0 overflow-hidden">
            <div
              className="flex items-center justify-between px-5 py-4 cursor-pointer hover:bg-slate-50 transition-colors"
              onClick={() => setExpandedCol(expandedCol === profile.column ? null : profile.column)}
            >
              <div className="flex items-center gap-3">
                <span className="font-mono text-sm font-medium text-slate-800">{profile.column}</span>
                <span className="badge bg-brand-50 text-brand-700 border border-brand-100">
                  {profile.frequency}
                </span>
                {profile.is_regular && (
                  <span className="badge bg-emerald-50 text-emerald-700 border border-emerald-100">
                    regular
                  </span>
                )}
              </div>
              <span className="text-xs text-slate-400">
                {profile.date_range_start} to {profile.date_range_end}
              </span>
            </div>

            {expandedCol === profile.column && (
              <div className="px-5 pb-5 border-t border-slate-100 pt-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <StatBox label="Total points" value={profile.total_points.toLocaleString()} />
                  <StatBox label="Frequency" value={profile.frequency} />
                  <StatBox
                    label="Regularity"
                    value={profile.is_regular ? 'Regular' : 'Irregular'}
                    color={profile.is_regular ? 'text-emerald-600' : 'text-amber-600'}
                  />
                  <StatBox label="Gaps" value={String(profile.gap_count)} color={profile.gap_count > 0 ? 'text-amber-600' : 'text-emerald-600'} />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                    <p className="text-[11px] text-slate-400 font-medium mb-1">Trend</p>
                    <p className={`text-sm font-semibold ${
                      profile.trend === 'increasing' ? 'text-emerald-600' :
                      profile.trend === 'decreasing' ? 'text-rose-600' : 'text-slate-600'
                    }`}>
                      {profile.trend === 'increasing' && 'Increasing'}
                      {profile.trend === 'decreasing' && 'Decreasing'}
                      {profile.trend === 'flat' && 'Flat / No trend'}
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                    <p className="text-[11px] text-slate-400 font-medium mb-1">Seasonality</p>
                    <p className="text-sm font-semibold text-slate-700">
                      {profile.has_seasonality
                        ? `Detected (period: ${profile.seasonality_period})`
                        : 'None detected'}
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                    <p className="text-[11px] text-slate-400 font-medium mb-1">Stationarity</p>
                    <p className={`text-sm font-semibold ${profile.is_stationary ? 'text-emerald-600' : 'text-amber-600'}`}>
                      {profile.is_stationary ? 'Stationary' : 'Non-stationary'}
                    </p>
                  </div>
                </div>

                {profile.gap_locations.length > 0 && (
                  <div className="mt-4 p-3 rounded-lg bg-amber-50 border border-amber-100">
                    <p className="text-xs font-semibold text-amber-700 mb-2">
                      Gap locations ({profile.gap_count} total)
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {profile.gap_locations.map((loc, i) => (
                        <span key={i} className="text-xs px-2 py-0.5 rounded bg-white border border-amber-200 text-amber-800">
                          {loc}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function StatBox({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
      <p className="text-[11px] text-slate-400 font-medium mb-0.5">{label}</p>
      <p className={`text-sm font-semibold ${color || 'text-slate-800'}`}>{value}</p>
    </div>
  );
}
