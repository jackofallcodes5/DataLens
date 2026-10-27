import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { datasetService } from '../services/datasetService';
import { 
  Table, 
  BarChart2, 
  Wand2, 
  Download, 
  AlertTriangle, 
  CheckCircle, 
  ChevronLeft, 
  ChevronRight,
  Info
} from 'lucide-react';

export default function DatasetPage({ onDatasetLoaded }) {
  const { datasetId } = useParams();
  const [dataset, setDataset] = useState(null);
  const [versions, setVersions] = useState([]);
  const [selectedVersionId, setSelectedVersionId] = useState('');
  const [profile, setProfile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [page, setPage] = useState(1);
  const [activeTab, setActiveTab] = useState('preview'); // 'preview' | 'profile'
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDatasetInfo();
  }, [datasetId]);

  useEffect(() => {
    if (datasetId && selectedVersionId) {
      loadDataForVersion(selectedVersionId, page);
    }
  }, [selectedVersionId, page]);

  const loadDatasetInfo = async () => {
    try {
      setLoading(true);
      const [dRes, vRes] = await Promise.all([
        datasetService.getDataset(datasetId),
        datasetService.getVersions(datasetId),
      ]);
      setDataset(dRes.data);
      setVersions(vRes.data);
      if (onDatasetLoaded) onDatasetLoaded(dRes.data);

      const activeVerId = dRes.data.latest_version_id || (vRes.data[0] && vRes.data[0].id);
      setSelectedVersionId(activeVerId);
    } catch (err) {
      setError('Failed to load dataset details.');
    } finally {
      setLoading(false);
    }
  };

  const loadDataForVersion = async (versionId, pageNum) => {
    try {
      const [prevRes, profRes] = await Promise.all([
        datasetService.getPreview(datasetId, versionId, pageNum, 50),
        datasetService.getProfile(datasetId, versionId),
      ]);
      setPreview(prevRes.data);
      setProfile(profRes.data);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-500 text-sm">Loading dataset workspace...</div>;
  }

  if (error || !dataset) {
    return (
      <div className="p-6 bg-red-50 text-red-700 rounded-xl border border-red-200">
        {error || 'Dataset not found.'}
      </div>
    );
  }

  const activeVersion = versions.find((v) => v.id === selectedVersionId) || versions[0];

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">{dataset.original_filename}</h1>
            <span className="px-2 py-0.5 rounded text-xs font-semibold bg-sky-100 text-sky-800">
              Version {activeVersion?.version_number}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Uploaded on {new Date(dataset.created_at).toLocaleString()} • {dataset.file_format.toUpperCase()}
          </p>
        </div>

        {/* Action Shortcuts */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Version Selector */}
          <div className="flex items-center gap-1.5 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200 text-xs">
            <span className="text-slate-500 font-medium">Version:</span>
            <select
              value={selectedVersionId}
              onChange={(e) => {
                setSelectedVersionId(e.target.value);
                setPage(1);
              }}
              className="bg-transparent font-semibold text-slate-800 focus:outline-none cursor-pointer"
            >
              {versions.map((v) => (
                <option key={v.id} value={v.id}>
                  v{v.version_number} ({v.operation_type})
                </option>
              ))}
            </select>
          </div>

          <Link
            to={`/datasets/${datasetId}/clean`}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-sky-600 text-white hover:bg-sky-700 transition"
          >
            <Wand2 className="w-3.5 h-3.5" />
            Clean Data
          </Link>

          <Link
            to={`/datasets/${datasetId}/visualize`}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-700 transition"
          >
            <BarChart2 className="w-3.5 h-3.5" />
            Visualize
          </Link>

          <Link
            to={`/datasets/${datasetId}/export`}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-white hover:bg-slate-900 transition"
          >
            <Download className="w-3.5 h-3.5" />
            Export
          </Link>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 gap-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab('preview')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition ${
            activeTab === 'preview'
              ? 'border-sky-600 text-sky-600 font-semibold'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Table className="w-4 h-4" />
          Data Preview & Explorer
        </button>
        <button
          onClick={() => setActiveTab('profile')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition ${
            activeTab === 'profile'
              ? 'border-sky-600 text-sky-600 font-semibold'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <BarChart2 className="w-4 h-4" />
          Quality Profile & Column Statistics
        </button>
      </div>

      {/* TAB 1: PREVIEW */}
      {activeTab === 'preview' && preview && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden space-y-4 p-4">
          <div className="flex items-center justify-between text-xs text-slate-500 px-2">
            <span>
              Showing rows {((page - 1) * preview.page_size) + 1} to{' '}
              {Math.min(page * preview.page_size, preview.total_rows)} of {preview.total_rows.toLocaleString()}
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="p-1 rounded bg-slate-100 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="font-semibold text-slate-700">Page {page}</span>
              <button
                disabled={page * preview.page_size >= preview.total_rows}
                onClick={() => setPage(page + 1)}
                className="p-1 rounded bg-slate-100 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="overflow-x-auto border border-slate-200 rounded-lg">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-100 border-b border-slate-200 text-slate-700 font-semibold">
                  <th className="py-2.5 px-4 w-12 text-center text-slate-400">#</th>
                  {preview.columns.map((col) => (
                    <th key={col} className="py-2.5 px-4 whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {preview.rows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50 transition">
                    <td className="py-2 px-4 text-center text-slate-400">
                      {((page - 1) * preview.page_size) + idx + 1}
                    </td>
                    {preview.columns.map((col) => {
                      const val = row[col];
                      const isNull = val === null || val === undefined;
                      return (
                        <td key={col} className="py-2 px-4 whitespace-nowrap">
                          {isNull ? (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-100 text-slate-400 italic">
                              NULL
                            </span>
                          ) : (
                            <span className="text-slate-800">{String(val)}</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: PROFILE & STATS */}
      {activeTab === 'profile' && profile && (
        <div className="space-y-6">
          {/* Summary KPI Badges */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
            <div className="bg-white p-3.5 rounded-lg border border-slate-200 text-center">
              <p className="text-[11px] text-slate-400 font-semibold uppercase">Total Rows</p>
              <p className="text-lg font-bold text-slate-800 mt-0.5">{profile.summary.total_rows}</p>
            </div>
            <div className="bg-white p-3.5 rounded-lg border border-slate-200 text-center">
              <p className="text-[11px] text-slate-400 font-semibold uppercase">Total Columns</p>
              <p className="text-lg font-bold text-slate-800 mt-0.5">{profile.summary.total_columns}</p>
            </div>
            <div className="bg-white p-3.5 rounded-lg border border-slate-200 text-center">
              <p className="text-[11px] text-slate-400 font-semibold uppercase">Duplicates</p>
              <p className={`text-lg font-bold mt-0.5 ${profile.summary.duplicate_rows > 0 ? 'text-amber-600' : 'text-slate-800'}`}>
                {profile.summary.duplicate_rows}
              </p>
            </div>
            <div className="bg-white p-3.5 rounded-lg border border-slate-200 text-center">
              <p className="text-[11px] text-slate-400 font-semibold uppercase">Missing Cells</p>
              <p className={`text-lg font-bold mt-0.5 ${profile.summary.total_missing_cells > 0 ? 'text-rose-600' : 'text-slate-800'}`}>
                {profile.summary.total_missing_cells} ({profile.summary.missing_percentage}%)
              </p>
            </div>
            <div className="bg-white p-3.5 rounded-lg border border-slate-200 text-center">
              <p className="text-[11px] text-slate-400 font-semibold uppercase">Numeric Cols</p>
              <p className="text-lg font-bold text-sky-600 mt-0.5">{profile.summary.numeric_columns_count}</p>
            </div>
            <div className="bg-white p-3.5 rounded-lg border border-slate-200 text-center">
              <p className="text-[11px] text-slate-400 font-semibold uppercase">Categorical</p>
              <p className="text-lg font-bold text-indigo-600 mt-0.5">{profile.summary.categorical_columns_count}</p>
            </div>
          </div>

          {/* Column Profile Table */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200">
              <h3 className="text-sm font-bold text-slate-900">Feature Statistics & Data Types</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                    <th className="py-3 px-4">Column Name</th>
                    <th className="py-3 px-4">Inferred Type</th>
                    <th className="py-3 px-4">Missing</th>
                    <th className="py-3 px-4">Distinct</th>
                    <th className="py-3 px-4">Min / Max</th>
                    <th className="py-3 px-4">Mean (Median)</th>
                    <th className="py-3 px-4">Frequent Example</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {profile.columns.map((col) => (
                    <tr key={col.column_name} className="hover:bg-slate-50 transition">
                      <td className="py-3 px-4 font-semibold text-slate-800">{col.column_name}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                          col.inferred_type === 'integer' || col.inferred_type === 'decimal'
                            ? 'bg-sky-100 text-sky-800'
                            : col.inferred_type === 'categorical'
                            ? 'bg-indigo-100 text-indigo-800'
                            : col.inferred_type === 'datetime'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-slate-100 text-slate-700'
                        }`}>
                          {col.inferred_type}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className={col.missing_count > 0 ? 'text-rose-600 font-semibold' : 'text-slate-600'}>
                          {col.missing_count} ({col.missing_percentage}%)
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-600">
                        {col.unique_count} ({col.unique_percentage}%)
                      </td>
                      <td className="py-3 px-4 text-slate-600">
                        {col.min !== null && col.max !== null ? `${col.min} to ${col.max}` : '-'}
                      </td>
                      <td className="py-3 px-4 text-slate-600">
                        {col.mean !== null ? `${col.mean} (${col.median})` : '-'}
                      </td>
                      <td className="py-3 px-4 text-slate-500 font-mono text-[11px]">
                        {col.most_frequent || (col.examples && col.examples[0]) || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
