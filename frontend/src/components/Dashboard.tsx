import { useState, useEffect } from 'react';
import { Upload, Globe } from 'lucide-react';
import { uploadFile, loadFromApi, getQualityScore } from '../api/client';
import QualityScoreView from './QualityScore';
import type { DatasetInfo, QualityScore } from '../types';

interface Props {
  dataset: DatasetInfo | null;
  onDatasetLoaded: (info: DatasetInfo) => void;
}

export default function Dashboard({ dataset, onDatasetLoaded }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [apiUrl, setApiUrl] = useState('');
  const [recordPath, setRecordPath] = useState('');
  const [qualityScore, setQualityScore] = useState<QualityScore | null>(null);

  useEffect(() => {
    if (dataset) {
      getQualityScore(dataset.id).then(setQualityScore).catch(console.error);
    } else {
      setQualityScore(null);
    }
  }, [dataset]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setError('');
    try {
      const info = await uploadFile(file);
      onDatasetLoaded(info);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadFromApi = async () => {
    if (!apiUrl.trim()) return;
    setLoading(true);
    setError('');
    try {
      const info = await loadFromApi(apiUrl.trim(), recordPath.trim() || undefined);
      onDatasetLoaded(info);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load from API');
    } finally {
      setLoading(false);
    }
  };

  if (!dataset) {
    return (
      <div className="max-w-2xl mx-auto py-8">
        <div className="text-center mb-10 p-8 rounded-2xl bg-gradient-to-br from-brand-600 to-brand-800 shadow-xl shadow-brand-900/20">
          <div className="w-14 h-14 rounded-2xl bg-white/15 flex items-center justify-center mx-auto mb-5">
            <span className="text-white text-2xl font-bold">D</span>
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Welcome to DataProfi</h2>
          <p className="text-brand-200 mt-2 text-sm max-w-md mx-auto">
            Upload a file or load data from any JSON API to start profiling
          </p>
        </div>

        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <span className="w-7 h-7 rounded-lg bg-brand-50 flex items-center justify-center text-brand-600"><Upload size={14} /></span>
              <label className="text-sm font-semibold text-slate-800">Upload CSV or JSON</label>
            </div>
            <div className="border-2 border-dashed border-slate-200 rounded-xl p-8 text-center hover:border-brand-300 hover:bg-brand-50/30 transition-all cursor-pointer">
              <input
                type="file"
                accept=".csv,.json"
                onChange={handleFileUpload}
                className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100 file:cursor-pointer cursor-pointer"
              />
              <p className="text-xs text-slate-400 mt-3">Supports .csv and .json files</p>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <span className="w-7 h-7 rounded-lg bg-brand-50 flex items-center justify-center text-brand-600"><Globe size={14} /></span>
              <label className="text-sm font-semibold text-slate-800">Load from JSON API</label>
            </div>
            <div className="space-y-3">
              <input
                type="text"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleLoadFromApi()}
                placeholder="https://api.example.com/data.json"
                className="input-field"
              />
              <div className="flex gap-2 items-end">
                <div className="flex-1">
                  <label className="text-xs text-slate-400 mb-1 block">Record path (optional)</label>
                  <input
                    type="text"
                    value={recordPath}
                    onChange={(e) => setRecordPath(e.target.value)}
                    placeholder="e.g. data.records or results"
                    className="input-field text-xs"
                  />
                </div>
                <button onClick={handleLoadFromApi} disabled={loading || !apiUrl.trim()} className="btn-primary">
                  {loading ? 'Loading...' : 'Load'}
                </button>
              </div>
              <p className="text-xs text-slate-400">
                Provide any URL that returns JSON. If the data is nested, specify the path to the records array.
              </p>
            </div>
          </div>
        </div>

        {loading && (
          <div className="text-center mt-6">
            <div className="inline-flex items-center gap-2 text-sm text-brand-600">
              <div className="w-4 h-4 border-2 border-brand-200 border-t-brand-600 rounded-full animate-spin" />
              Loading dataset...
            </div>
          </div>
        )}
        {error && (
          <div className="mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200">
            <p className="text-sm text-rose-700 text-center">{error}</p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {qualityScore && <QualityScoreView score={qualityScore} datasetId={dataset.id} />}
    </div>
  );
}
