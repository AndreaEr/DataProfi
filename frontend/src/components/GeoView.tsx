import { useState, useEffect } from 'react';
import { getGeoProfile } from '../api/client';
import type { GeoReport } from '../api/client';

interface Props {
  datasetId: string;
}

export default function GeoView({ datasetId }: Props) {
  const [report, setReport] = useState<GeoReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getGeoProfile(datasetId)
      .then(setReport)
      .finally(() => setLoading(false));
  }, [datasetId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="flex items-center gap-2 text-sm text-brand-600">
          <div className="w-4 h-4 border-2 border-brand-200 border-t-brand-600 rounded-full animate-spin" />
          Analyzing spatial data...
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
        <p className="text-slate-600 font-medium">No geographic columns detected</p>
        <p className="text-sm text-slate-400 mt-1">
          This dataset does not contain recognizable latitude/longitude column pairs.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-slate-900">Spatial Analysis</h2>
        <span className="text-sm text-slate-500">
          {report.detected_pairs.length} coordinate pair{report.detected_pairs.length !== 1 ? 's' : ''} detected
        </span>
      </div>

      {report.profiles.map((profile, idx) => (
        <div key={idx} className="space-y-4">
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <span className="font-mono text-sm font-medium text-slate-800">
                {profile.column_lat} / {profile.column_lng}
              </span>
              <span className="badge bg-brand-50 text-brand-700 border border-brand-100">
                {profile.valid_points} valid points
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <StatBox label="Total points" value={profile.total_points.toLocaleString()} />
              <StatBox label="Valid" value={`${profile.valid_points} (${Math.round(profile.valid_points / profile.total_points * 100)}%)`} />
              <StatBox label="Spatial spread" value={`${profile.spatial_spread_km} km`} />
              <StatBox label="Density" value={`${profile.density_points_per_sq_km.toFixed(1)} pts/km2`} />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="card">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
                Centroid
              </p>
              <div className="grid grid-cols-2 gap-3">
                <StatBox label="Latitude" value={profile.centroid_lat.toFixed(6)} />
                <StatBox label="Longitude" value={profile.centroid_lng.toFixed(6)} />
              </div>
            </div>

            <div className="card">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
                Bounding Box
              </p>
              {profile.bounding_box && (
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2 rounded bg-slate-50 border border-slate-100">
                    <span className="text-slate-400">N: </span>
                    <span className="font-mono text-slate-700">{profile.bounding_box.max_lat?.toFixed(4)}</span>
                  </div>
                  <div className="p-2 rounded bg-slate-50 border border-slate-100">
                    <span className="text-slate-400">S: </span>
                    <span className="font-mono text-slate-700">{profile.bounding_box.min_lat?.toFixed(4)}</span>
                  </div>
                  <div className="p-2 rounded bg-slate-50 border border-slate-100">
                    <span className="text-slate-400">E: </span>
                    <span className="font-mono text-slate-700">{profile.bounding_box.max_lng?.toFixed(4)}</span>
                  </div>
                  <div className="p-2 rounded bg-slate-50 border border-slate-100">
                    <span className="text-slate-400">W: </span>
                    <span className="font-mono text-slate-700">{profile.bounding_box.min_lng?.toFixed(4)}</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {profile.invalid_reasons.length > 0 && (
            <div className="p-4 rounded-xl bg-amber-50 border border-amber-200">
              <p className="text-sm font-semibold text-amber-800 mb-2">Spatial quality issues</p>
              <ul className="space-y-1">
                {profile.invalid_reasons.map((reason, i) => (
                  <li key={i} className="text-sm text-amber-700 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 bg-amber-400 rounded-full flex-shrink-0" />
                    {reason}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {profile.outlier_count > 0 && profile.outlier_details && (
            <div className="card border-rose-200">
              <p className="text-xs font-semibold text-rose-600 uppercase tracking-wide mb-3">
                Spatial Outliers ({profile.outlier_count})
              </p>
              <div className="space-y-2">
                {profile.outlier_details.map((detail, di) => (
                  <div key={di} className="p-3 rounded-lg border border-rose-100 bg-rose-50/30">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-slate-500">Row {detail.row}</span>
                      <span className="text-xs font-mono font-semibold text-rose-600">
                        {detail.distance_from_centre_km} km from centre
                      </span>
                    </div>
                    <p className="text-xs text-slate-600">{detail.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {profile.clusters.length > 0 && (
            <div className="card">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                Spatial Clusters ({profile.cluster_count})
              </p>
              <p className="text-xs text-slate-400 mb-3">
                Data points are grouped into {profile.cluster_count} geographic clusters based on proximity.
              </p>
              <div className="space-y-2">
                {profile.clusters.map((cluster, ci) => (
                  <div key={ci} className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-slate-700">{cluster.label}</span>
                      <span className="badge bg-brand-50 text-brand-700 border border-brand-100">
                        {cluster.point_count} points
                      </span>
                    </div>
                    <p className="text-xs text-slate-500">
                      Centre: {cluster.centroid_lat.toFixed(4)}, {cluster.centroid_lng.toFixed(4)} - spread: {cluster.avg_spread_km} km
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function StatBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
      <p className="text-[11px] text-slate-400 font-medium mb-0.5">{label}</p>
      <p className="text-sm font-semibold text-slate-800">{value}</p>
    </div>
  );
}
