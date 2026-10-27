import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { datasetService } from '../services/datasetService';
import { Download, FileSpreadsheet, FileText, CheckCircle2, ShieldCheck } from 'lucide-react';

export default function ExportPage() {
  const { datasetId } = useParams();
  const [dataset, setDataset] = useState(null);
  const [versions, setVersions] = useState([]);
  const [selectedVerId, setSelectedVerId] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInfo();
  }, [datasetId]);

  const loadInfo = async () => {
    try {
      setLoading(true);
      const [dRes, vRes] = await Promise.all([
        datasetService.getDataset(datasetId),
        datasetService.getVersions(datasetId),
      ]);
      setDataset(dRes.data);
      setVersions(vRes.data);
      setSelectedVerId(dRes.data.latest_version_id || (vRes.data[0] && vRes.data[0].id));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !dataset) {
    return <div className="p-8 text-center text-sm text-slate-500">Loading export suite...</div>;
  }

  const activeVer = versions.find((v) => v.id === selectedVerId) || versions[0];

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">Export Cleaned Data & Quality Reports</h1>
        <p className="text-sm text-slate-500 mt-1">
          Download sanitized CSV, Excel workbooks, or comprehensive JSON audit reports for version {activeVer?.version_number}.
        </p>
      </div>

      {/* Version Picker */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
        <div>
          <label className="block text-xs font-semibold text-slate-700">Select Dataset Version to Export</label>
          <p className="text-xs text-slate-400">Target specific point-in-time cleaning output.</p>
        </div>
        <select
          value={selectedVerId}
          onChange={(e) => setSelectedVerId(e.target.value)}
          className="text-xs font-semibold rounded-lg border border-slate-300 p-2 focus:ring-1 focus:ring-sky-500 bg-slate-50"
        >
          {versions.map((v) => (
            <option key={v.id} value={v.id}>
              v{v.version_number} ({v.operation_type})
            </option>
          ))}
        </select>
      </div>

      {/* Export Options Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* CSV Export */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between space-y-4">
          <div>
            <div className="w-10 h-10 bg-emerald-50 text-emerald-600 rounded-lg flex items-center justify-center mb-3">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">Standard CSV</h3>
            <p className="text-xs text-slate-500 mt-1">
              Comma-separated file with formula injection mitigation and UTF-8 encoding.
            </p>
          </div>
          <a
            href={datasetService.getExportUrl(datasetId, 'csv', selectedVerId)}
            download
            className="w-full py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-lg transition text-center flex items-center justify-center gap-1.5 shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            Download CSV
          </a>
        </div>

        {/* Excel XLSX Export */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between space-y-4">
          <div>
            <div className="w-10 h-10 bg-sky-50 text-sky-600 rounded-lg flex items-center justify-center mb-3">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">Excel Workbook</h3>
            <p className="text-xs text-slate-500 mt-1">
              Microsoft Excel (.xlsx) format with auto-fitted column dimensions.
            </p>
          </div>
          <a
            href={datasetService.getExportUrl(datasetId, 'xlsx', selectedVerId)}
            download
            className="w-full py-2 bg-sky-600 hover:bg-sky-700 text-white font-semibold text-xs rounded-lg transition text-center flex items-center justify-center gap-1.5 shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            Download XLSX
          </a>
        </div>

        {/* Audit Quality Report */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between space-y-4">
          <div>
            <div className="w-10 h-10 bg-indigo-50 text-indigo-600 rounded-lg flex items-center justify-center mb-3">
              <FileText className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">Quality Audit Report</h3>
            <p className="text-xs text-slate-500 mt-1">
              Complete JSON export containing dataset profile stats, detected issues, and full operation logs.
            </p>
          </div>
          <a
            href={datasetService.getExportUrl(datasetId, 'report', selectedVerId)}
            target="_blank"
            rel="noreferrer"
            className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-lg transition text-center flex items-center justify-center gap-1.5 shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            Download Report
          </a>
        </div>
      </div>

      {/* Security Banner */}
      <div className="p-4 bg-slate-100 rounded-xl border border-slate-200 flex items-start gap-3 text-xs text-slate-600">
        <ShieldCheck className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-slate-800">Formula Injection Mitigation Enabled: </span>
          Values starting with special formula triggers (=, +, -, @) are automatically escaped with single quotes to protect downstream spreadsheet software from command execution.
        </div>
      </div>
    </div>
  );
}
