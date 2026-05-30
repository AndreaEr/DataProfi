import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from 'recharts';
import ReportDownload from './ReportDownload';
import type { QualityScore } from '../types';

interface Props {
  score?: QualityScore;
  datasetId?: string;
}

export default function QualityScoreView({ score, datasetId }: Props) {
  if (!score) return null;

  const radarData = Object.entries(score.dimension_scores).map(([key, value]) => ({
    dimension: key.charAt(0).toUpperCase() + key.slice(1),
    score: value,
    fullMark: 100,
  }));

  const getScoreColor = (s: number) => {
    if (s >= 80) return 'text-emerald-600';
    if (s >= 60) return 'text-amber-600';
    return 'text-rose-600';
  };

  const getBarColor = (s: number) => {
    if (s >= 80) return 'bg-emerald-500';
    if (s >= 60) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  const getBarBgColor = (s: number) => {
    if (s >= 80) return 'bg-emerald-100';
    if (s >= 60) return 'bg-amber-100';
    return 'bg-rose-100';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-slate-900">Quality Overview</h2>
        {datasetId && <ReportDownload datasetId={datasetId} />}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="stat-card text-center">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
            Overall Score
          </p>
          <p className={`text-5xl font-bold ${getScoreColor(score.overall_score)}`}>
            {score.overall_score.toFixed(0)}
          </p>
          <p className="text-xs text-slate-400 mt-1">out of 100</p>
        </div>

        <div className="stat-card">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
            Dataset Info
          </p>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-slate-500">Rows</span>
              <span className="text-sm font-semibold text-slate-800">{score.row_count.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-slate-500">Columns</span>
              <span className="text-sm font-semibold text-slate-800">{score.column_count}</span>
            </div>
          </div>
        </div>

        <div className="stat-card">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
            Needs Attention
          </p>
          <div className="space-y-1.5">
            {score.worst_columns.slice(0, 4).map((col) => (
              <p key={col} className="text-sm text-slate-700 font-mono truncate flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-amber-400 rounded-full flex-shrink-0" />
                {col}
              </p>
            ))}
            {score.worst_columns.length === 0 && (
              <p className="text-sm text-slate-400 flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
                All columns look good
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">
            Quality Dimensions
          </p>
          <ResponsiveContainer width="100%" height={260}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 11, fill: '#64748b' }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 9, fill: '#94a3b8' }} />
              <Radar
                name="Score"
                dataKey="score"
                stroke="#2563eb"
                fill="#3b82f6"
                fillOpacity={0.15}
                strokeWidth={2}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">
            Score Breakdown
          </p>
          <div className="space-y-4">
            {Object.entries(score.dimension_scores).map(([dim, val]) => (
              <div key={dim}>
                <div className="flex justify-between text-sm mb-1.5">
                  <span className="capitalize text-slate-600 font-medium">{dim}</span>
                  <span className={`font-semibold ${getScoreColor(val)}`}>{val.toFixed(1)}</span>
                </div>
                <div className={`w-full rounded-full h-2 ${getBarBgColor(val)}`}>
                  <div
                    className={`h-2 rounded-full transition-all ${getBarColor(val)}`}
                    style={{ width: `${val}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {score.suggested_fixes.length > 0 && (
        <div className="card">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">
            Suggested Fixes ({score.suggested_fixes.length})
          </p>
          <div className="space-y-2 max-h-56 overflow-y-auto">
            {score.suggested_fixes.map((fix, i) => (
              <div key={i} className="flex items-start gap-3 text-sm py-2.5 border-b border-slate-100 last:border-0">
                <span className="badge bg-brand-50 text-brand-700 font-mono">
                  {fix.column}
                </span>
                <span className="text-slate-600">{fix.issue}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
