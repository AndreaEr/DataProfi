import { useState, useCallback } from 'react';
import * as api from '../api/client';
import type {
  DatasetInfo,
  ColumnProfile,
  QualityScore,
  IndexRecommendation,
  MLReadiness,
  CleanResponse,
} from '../types';

export function useDataProfi() {
  const [dataset, setDataset] = useState<DatasetInfo | null>(null);
  const [profiles, setProfiles] = useState<ColumnProfile[]>([]);
  const [score, setScore] = useState<QualityScore | null>(null);
  const [indexes, setIndexes] = useState<IndexRecommendation[]>([]);
  const [mlReadiness, setMLReadiness] = useState<MLReadiness | null>(null);
  const [cleanResult, setCleanResult] = useState<CleanResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDataset = useCallback(async (file?: File, apiUrl?: string) => {
    setLoading(true);
    setError(null);
    try {
      let info: DatasetInfo;
      if (file) {
        info = await api.uploadFile(file);
      } else if (apiUrl) {
        info = await api.loadFromApi(apiUrl);
      } else {
        throw new Error('Provide either a file or an API URL');
      }
      setDataset(info);
      return info;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Load failed');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const analyze = useCallback(async (datasetId: string) => {
    setLoading(true);
    try {
      const [profileData, scoreData, indexData, mlData] = await Promise.all([
        api.getProfile(datasetId),
        api.getQualityScore(datasetId),
        api.getIndexRecommendations(datasetId),
        api.getMLReadiness(datasetId),
      ]);
      setProfiles(profileData);
      setScore(scoreData);
      setIndexes(indexData);
      setMLReadiness(mlData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  }, []);

  const clean = useCallback(
    async (datasetId: string, steps: Array<{ step_type: string; [key: string]: unknown }>) => {
      setLoading(true);
      try {
        const result = await api.cleanDataset(datasetId, steps);
        setCleanResult(result);
        return result;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Cleaning failed');
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return {
    dataset,
    profiles,
    score,
    indexes,
    mlReadiness,
    cleanResult,
    loading,
    error,
    loadDataset,
    analyze,
    clean,
  };
}
