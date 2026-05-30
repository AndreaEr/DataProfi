import type {
  DatasetInfo,
  ColumnProfile,
  QualityScore,
  IndexRecommendation,
  MLReadiness,
  CleanResponse,
  EnhancedColumnProfile,
  TimeseriesReport,
  CorrelationReport,
  DetailedQualityScore,
} from '../types';

const BASE = '/api';

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || 'API request failed');
  }
  return res.json();
}

export async function uploadFile(file: File): Promise<DatasetInfo> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${BASE}/ingest/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Upload failed');
  return res.json();
}

export async function loadFromApi(url: string, recordPath?: string): Promise<DatasetInfo> {
  return fetchJSON('/ingest/api', {
    method: 'POST',
    body: JSON.stringify({ url, record_path: recordPath || null, limit: 5000 }),
  });
}

export async function getProfile(datasetId: string): Promise<ColumnProfile[]> {
  return fetchJSON(`/profile/${datasetId}`);
}

export async function getQualityScore(datasetId: string): Promise<QualityScore> {
  return fetchJSON(`/profile/${datasetId}/score`);
}

export async function getIndexRecommendations(
  datasetId: string,
  tableName = 'table'
): Promise<IndexRecommendation[]> {
  return fetchJSON(`/index/${datasetId}/recommend?table_name=${tableName}`);
}

export async function getMLReadiness(datasetId: string): Promise<MLReadiness> {
  return fetchJSON(`/ml/${datasetId}/readiness`);
}

export async function cleanDataset(
  datasetId: string,
  steps: Array<{ step_type: string; [key: string]: unknown }>
): Promise<CleanResponse> {
  return fetchJSON(`/clean/${datasetId}`, {
    method: 'POST',
    body: JSON.stringify({ steps }),
  });
}

export async function listDatasets(): Promise<DatasetInfo[]> {
  return fetchJSON('/datasets');
}

export async function getEnhancedProfile(datasetId: string): Promise<EnhancedColumnProfile[]> {
  return fetchJSON(`/profile/${datasetId}/enhanced`);
}

export async function getTimeseriesProfile(datasetId: string): Promise<TimeseriesReport> {
  return fetchJSON(`/profile/${datasetId}/timeseries`);
}

export async function getCorrelations(datasetId: string): Promise<CorrelationReport> {
  return fetchJSON(`/profile/${datasetId}/correlations`);
}

export async function getDetailedQualityScore(datasetId: string): Promise<DetailedQualityScore> {
  return fetchJSON(`/profile/${datasetId}/score/detailed`);
}

export interface OutlierContext {
  normal_min: number;
  normal_max: number;
  mean: number;
  q1: number;
  q3: number;
  method: string;
}

export interface OutlierDetail {
  column: string;
  outlier_count: number;
  context: OutlierContext;
  rows: Array<Record<string, string | number | null>>;
}

export async function getOutlierDetails(datasetId: string, column: string): Promise<OutlierDetail> {
  return fetchJSON(`/profile/${datasetId}/outliers/${encodeURIComponent(column)}`);
}

export interface IssueGroup {
  type: string;
  label: string;
  count: number;
  rows: Array<Record<string, string | null>>;
}

export interface ColumnIssues {
  column: string;
  issues: IssueGroup[];
}

export async function getColumnIssues(datasetId: string, column: string, issueType = 'all'): Promise<ColumnIssues> {
  return fetchJSON(`/profile/${datasetId}/issues/${encodeURIComponent(column)}?issue_type=${issueType}`);
}

export interface DataPreview {
  columns: string[];
  total_rows: number;
  rows: string[][];
}

export async function getDataPreview(datasetId: string, rows = 10): Promise<DataPreview> {
  return fetchJSON(`/dataset/${datasetId}/preview?rows=${rows}`);
}

export function getDownloadUrl(datasetId: string): string {
  return `/api/dataset/${datasetId}/download`;
}

export async function getMethodology(): Promise<Record<string, unknown>> {
  return fetchJSON('/methodology');
}

export interface GeoOutlierDetail {
  row: number;
  latitude: number;
  longitude: number;
  distance_from_centre_km: number;
  reason: string;
}

export interface GeoProfile {
  column_lat: string;
  column_lng: string;
  total_points: number;
  valid_points: number;
  invalid_count: number;
  invalid_reasons: string[];
  centroid_lat: number;
  centroid_lng: number;
  bounding_box: { min_lat: number; max_lat: number; min_lng: number; max_lng: number };
  spatial_spread_km: number;
  density_points_per_sq_km: number;
  outlier_count: number;
  outlier_indices: number[];
  outlier_details: GeoOutlierDetail[];
  cluster_count: number;
  clusters: Array<{ centroid_lat: number; centroid_lng: number; point_count: number; avg_spread_km: number; label: string }>;
}

export interface GeoReport {
  detected_pairs: Array<[string, string]>;
  profiles: GeoProfile[];
}

export async function getGeoProfile(datasetId: string): Promise<GeoReport> {
  return fetchJSON(`/profile/${datasetId}/geo`);
}

export interface ColumnSchemaInfo {
  name: string;
  pg_type: string;
  nullable: boolean;
  is_primary_key: boolean;
  is_unique: boolean;
  check_constraint: string | null;
  comment: string | null;
}

export interface ForeignKeyHint {
  column: string;
  references_table: string;
  references_column: string;
  confidence: number;
  reason: string;
}

export interface NormalizationHint {
  column: string;
  unique_values: number;
  total_rows: number;
  suggestion: string;
}

export interface SchemaRecommendation {
  table_name: string;
  columns: ColumnSchemaInfo[];
  primary_key: string | null;
  unique_constraints: string[];
  foreign_key_hints: ForeignKeyHint[];
  normalization_hints: NormalizationHint[];
  ddl: string;
}

export async function getSchemaRecommendation(datasetId: string, tableName = 'my_table'): Promise<SchemaRecommendation> {
  return fetchJSON(`/profile/${datasetId}/schema?table_name=${encodeURIComponent(tableName)}`);
}
