import { useState, useEffect } from 'react';
import { getSchemaRecommendation } from '../api/client';
import type { SchemaRecommendation } from '../api/client';

interface Props {
  datasetId: string;
}

export default function SchemaView({ datasetId }: Props) {
  const [schema, setSchema] = useState<SchemaRecommendation | null>(null);
  const [loading, setLoading] = useState(true);
  const [tableName, setTableName] = useState('my_table');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setLoading(true);
    getSchemaRecommendation(datasetId, tableName)
      .then(setSchema)
      .finally(() => setLoading(false));
  }, [datasetId, tableName]);

  const copyDDL = () => {
    if (schema?.ddl) {
      navigator.clipboard.writeText(schema.ddl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="flex items-center gap-2 text-sm text-brand-600">
          <div className="w-4 h-4 border-2 border-brand-200 border-t-brand-600 rounded-full animate-spin" />
          Generating schema...
        </div>
      </div>
    );
  }

  if (!schema) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-slate-900">Schema Design</h2>
        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-500">Table name:</label>
          <input
            type="text"
            value={tableName}
            onChange={(e) => setTableName(e.target.value)}
            className="input-field text-xs w-40"
          />
        </div>
      </div>

      {/* Column definitions table */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/50">
                <th className="px-4 py-3 text-left font-semibold text-slate-500 uppercase tracking-wide">Column</th>
                <th className="px-4 py-3 text-left font-semibold text-slate-500 uppercase tracking-wide">Type</th>
                <th className="px-4 py-3 text-left font-semibold text-slate-500 uppercase tracking-wide">Nullable</th>
                <th className="px-4 py-3 text-left font-semibold text-slate-500 uppercase tracking-wide">Constraints</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {schema.columns.map((col) => (
                <tr key={col.name} className="hover:bg-slate-50">
                  <td className="px-4 py-2.5 font-mono text-slate-800 font-medium">
                    {col.name}
                    {col.is_primary_key && (
                      <span className="ml-2 badge bg-brand-50 text-brand-700 border border-brand-100 text-[10px]">PK</span>
                    )}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-brand-700">{col.pg_type}</td>
                  <td className="px-4 py-2.5">
                    <span className={col.nullable ? 'text-slate-400' : 'text-slate-700 font-medium'}>
                      {col.nullable ? 'NULL' : 'NOT NULL'}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-slate-600">
                    {col.is_unique && <span className="badge bg-indigo-50 text-indigo-700 border border-indigo-100 mr-1">UNIQUE</span>}
                    {col.check_constraint && (
                      <span className="font-mono text-[11px] text-slate-500">{col.check_constraint}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* DDL output */}
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
            Generated DDL
          </p>
          <button onClick={copyDDL} className="btn-secondary text-xs">
            {copied ? 'Copied' : 'Copy SQL'}
          </button>
        </div>
        <pre className="bg-slate-900 text-slate-100 rounded-lg p-4 text-xs font-mono overflow-x-auto whitespace-pre-wrap">
          {schema.ddl}
        </pre>
      </div>

      {/* Foreign key hints */}
      {schema.foreign_key_hints.length > 0 && (
        <div className="card">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
            Potential Foreign Keys ({schema.foreign_key_hints.length})
          </p>
          <div className="space-y-2">
            {schema.foreign_key_hints.map((fk, i) => (
              <div key={i} className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-slate-700">
                    <span className="font-mono font-medium">{fk.column}</span>
                    {' references '}
                    <span className="font-mono font-medium">{fk.references_table}.{fk.references_column}</span>
                  </span>
                  <span className="badge bg-brand-50 text-brand-700 border border-brand-100">
                    {(fk.confidence * 100).toFixed(0)}% confidence
                  </span>
                </div>
                <p className="text-xs text-slate-500">{fk.reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Normalization hints */}
      {schema.normalization_hints.length > 0 && (
        <div className="card">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
            Normalization Suggestions
          </p>
          <div className="space-y-2">
            {schema.normalization_hints.map((nh, i) => (
              <div key={i} className="p-3 rounded-lg bg-amber-50 border border-amber-200">
                <p className="text-sm text-amber-800">{nh.suggestion}</p>
                <p className="text-xs text-amber-600 mt-1">
                  {nh.unique_values} unique values across {nh.total_rows} rows
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
