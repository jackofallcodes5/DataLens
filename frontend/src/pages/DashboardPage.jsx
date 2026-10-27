import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { datasetService } from '../services/datasetService';
import { Database, UploadCloud, Layers, AlertCircle, ArrowRight, Table, CheckCircle2 } from 'lucide-react';

export default function DashboardPage() {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      setLoading(true);
      const res = await datasetService.getDatasets();
      setDatasets(res.data);
    } catch (err) {
      setError('Failed to load datasets from the backend.');
    } finally {
      setLoading(false);
    }
  };

  const totalRows = datasets.reduce((acc, d) => acc + (d.row_count || 0), 0);
  const totalCols = datasets.reduce((acc, d) => acc + (d.column_count || 0), 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Overview Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">
            Data quality monitoring, cleaning operations, and analytics workspace.
          </p>
        </div>
        <Link
          to="/upload"
          className="inline-flex items-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white font-medium text-sm rounded-lg shadow-sm transition"
        >
          <UploadCloud className="w-4 h-4" />
          Upload Dataset
        </Link>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase text-slate-400">Total Datasets</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-1">{datasets.length}</h3>
          </div>
          <div className="w-11 h-11 bg-sky-50 text-sky-600 rounded-lg flex items-center justify-center">
            <Database className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase text-slate-400">Indexed Rows</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-1">{totalRows.toLocaleString()}</h3>
          </div>
          <div className="w-11 h-11 bg-emerald-50 text-emerald-600 rounded-lg flex items-center justify-center">
            <Table className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase text-slate-400">Total Features (Cols)</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-1">{totalCols.toLocaleString()}</h3>
          </div>
          <div className="w-11 h-11 bg-indigo-50 text-indigo-600 rounded-lg flex items-center justify-center">
            <Layers className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Datasets Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900">Recent Datasets</h2>
          <span className="text-xs font-medium text-slate-400">Real Persistent Records</span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-sm text-slate-500">Loading datasets...</div>
        ) : datasets.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-14 h-14 bg-slate-100 text-slate-400 rounded-full flex items-center justify-center mx-auto mb-3">
              <Database className="w-7 h-7" />
            </div>
            <h3 className="text-base font-semibold text-slate-800">No datasets uploaded yet</h3>
            <p className="text-sm text-slate-500 mt-1 max-w-sm mx-auto">
              Upload a CSV or Excel dataset to inspect quality issues, clean missing values, and generate charts.
            </p>
            <Link
              to="/upload"
              className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-sky-600 text-white rounded-lg text-sm font-medium hover:bg-sky-700 transition"
            >
              <UploadCloud className="w-4 h-4" />
              Upload Now
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
                  <th className="py-3 px-6">Dataset Name</th>
                  <th className="py-3 px-6">Format</th>
                  <th className="py-3 px-6">Rows</th>
                  <th className="py-3 px-6">Columns</th>
                  <th className="py-3 px-6">Uploaded</th>
                  <th className="py-3 px-6 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {datasets.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3.5 px-6 font-medium text-slate-800">
                      <Link to={`/datasets/${d.id}`} className="hover:text-sky-600 flex items-center gap-2">
                        <Table className="w-4 h-4 text-slate-400" />
                        {d.original_filename}
                      </Link>
                    </td>
                    <td className="py-3.5 px-6">
                      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700 uppercase">
                        {d.file_format}
                      </span>
                    </td>
                    <td className="py-3.5 px-6 text-slate-600">{d.row_count?.toLocaleString()}</td>
                    <td className="py-3.5 px-6 text-slate-600">{d.column_count}</td>
                    <td className="py-3.5 px-6 text-slate-400 text-xs">
                      {new Date(d.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-6 text-right">
                      <Link
                        to={`/datasets/${d.id}`}
                        className="inline-flex items-center gap-1 text-sky-600 hover:text-sky-800 font-medium text-xs"
                      >
                        Open Workspace <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
