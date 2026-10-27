import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { datasetService } from '../services/datasetService';
import { 
  Wand2, 
  RotateCcw, 
  AlertTriangle, 
  CheckCircle, 
  ArrowRight, 
  HelpCircle,
  Clock,
  Sparkles,
  Info
} from 'lucide-react';

export default function CleaningPage({ onDatasetMutated }) {
  const { datasetId } = useParams();
  const [dataset, setDataset] = useState(null);
  const [issues, setIssues] = useState([]);
  const [history, setHistory] = useState([]);
  const [columns, setColumns] = useState([]);
  const [loading, setLoading] = useState(true);

  // Cleaning Form State
  const [operationType, setOperationType] = useState('remove_duplicates');
  const [selectedColumn, setSelectedColumn] = useState('');
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [strategy, setStrategy] = useState('median');
  const [constantVal, setConstantVal] = useState('');
  const [casingType, setCasingType] = useState('lower');
  const [targetType, setTargetType] = useState('integer');
  const [outlierAction, setOutlierAction] = useState('remove');
  const [filterOp, setFilterOp] = useState('equals');
  const [filterVal, setFilterVal] = useState('');
  const [renameNew, setRenameNew] = useState('');

  // Preview & Result State
  const [previewData, setPreviewData] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [applyLoading, setApplyLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    loadPageData();
  }, [datasetId]);

  const loadPageData = async () => {
    try {
      setLoading(true);
      const [dRes, iRes, hRes, pRes] = await Promise.all([
        datasetService.getDataset(datasetId),
        datasetService.getIssues(datasetId),
        datasetService.getHistory(datasetId),
        datasetService.getProfile(datasetId),
      ]);
      setDataset(dRes.data);
      setIssues(iRes.data);
      setHistory(hRes.data);
      const colNames = pRes.data.columns.map((c) => c.column_name);
      setColumns(colNames);
      if (colNames.length > 0 && !selectedColumn) {
        setSelectedColumn(colNames[0]);
      }
    } catch (err) {
      setErrorMessage('Failed to load dataset cleaning workspace.');
    } finally {
      setLoading(false);
    }
  };

  const getParameters = () => {
    switch (operationType) {
      case 'remove_duplicates':
        return { columns: selectedColumns.length > 0 ? selectedColumns : null, keep: 'first' };
      case 'handle_missing_values':
        return { column: selectedColumn, strategy, value: constantVal };
      case 'trim_whitespace':
        return { columns: selectedColumns.length > 0 ? selectedColumns : null };
      case 'normalize_case':
        return { columns: selectedColumns.length > 0 ? selectedColumns : [selectedColumn], case: casingType };
      case 'convert_data_types':
        return { column: selectedColumn, target_type: targetType, on_error: 'coerce' };
      case 'remove_columns':
        return { columns: selectedColumns.length > 0 ? selectedColumns : [selectedColumn] };
      case 'rename_column':
        return { old_name: selectedColumn, new_name: renameNew };
      case 'filter_rows':
        return { column: selectedColumn, operator: filterOp, value: filterVal };
      case 'handle_outliers':
        return { column: selectedColumn, action: outlierAction };
      default:
        return {};
    }
  };

  const handlePreview = async () => {
    try {
      setPreviewLoading(true);
      setErrorMessage(null);
      const params = getParameters();
      const res = await datasetService.previewCleaning(datasetId, operationType, params);
      setPreviewData(res.data);
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Failed to generate cleaning preview.');
      setPreviewData(null);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleApply = async () => {
    try {
      setApplyLoading(true);
      setErrorMessage(null);
      const params = getParameters();
      const res = await datasetService.applyCleaning(datasetId, operationType, params);
      setStatusMessage(res.data.summary?.message || 'Operation successfully executed.');
      setPreviewData(null);
      await loadPageData();
      if (onDatasetMutated) onDatasetMutated();
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Failed to apply cleaning transformation.');
    } finally {
      setApplyLoading(false);
    }
  };

  const handleUndo = async () => {
    try {
      setApplyLoading(true);
      setErrorMessage(null);
      const res = await datasetService.undoCleaning(datasetId);
      setStatusMessage(`Restored previous dataset version v${res.data.version_number}.`);
      setPreviewData(null);
      await loadPageData();
      if (onDatasetMutated) onDatasetMutated();
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Failed to undo operation.');
    } finally {
      setApplyLoading(false);
    }
  };

  const selectIssueSuggestion = (issue) => {
    if (issue.category === 'duplicates') {
      setOperationType('remove_duplicates');
    } else if (issue.category === 'missing_values') {
      setOperationType('handle_missing_values');
      setSelectedColumn(issue.column_name);
      setStrategy(issue.suggested_action === 'fill_median' ? 'median' : 'mode');
    } else if (issue.category === 'whitespace') {
      setOperationType('trim_whitespace');
      setSelectedColumns([issue.column_name]);
    } else if (issue.category === 'inconsistent_casing') {
      setOperationType('normalize_case');
      setSelectedColumns([issue.column_name]);
      setCasingType('lower');
    } else if (issue.category === 'outliers') {
      setOperationType('handle_outliers');
      setSelectedColumn(issue.column_name);
      setOutlierAction('remove');
    } else if (issue.category === 'empty_column') {
      setOperationType('remove_columns');
      setSelectedColumns([issue.column_name]);
    }
    setPreviewData(null);
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-500 text-sm">Loading cleaning studio...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Cleaning Studio & Transformation Engine</h1>
          <p className="text-sm text-slate-500 mt-1">
            Apply safe, non-destructive cleaning transformations with full atomic versioning and undo history.
          </p>
        </div>
        <button
          onClick={handleUndo}
          disabled={applyLoading}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition shadow-sm"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Undo Last Operation
        </button>
      </div>

      {statusMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <span>{statusMessage}</span>
          </div>
          <button onClick={() => setStatusMessage(null)} className="text-xs text-emerald-700 hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-xs text-red-700 hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Grid: Issues (Left) + Form/Preview (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Detected Issues */}
        <div className="space-y-4">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-500" />
                Detected Issues ({issues.length})
              </h2>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Click an issue to populate recommended cleaning configuration.
            </p>

            {issues.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-400 bg-slate-50 rounded-lg">
                No data quality issues detected in this version.
              </div>
            ) : (
              <div className="space-y-2.5 max-h-[500px] overflow-y-auto pr-1">
                {issues.map((issue) => (
                  <div
                    key={issue.id}
                    onClick={() => selectIssueSuggestion(issue)}
                    className="p-3 rounded-lg border border-slate-200 hover:border-sky-500 hover:bg-sky-50/40 cursor-pointer transition text-xs"
                  >
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <span className="font-semibold text-slate-800 truncate">
                        {issue.column_name ? `${issue.column_name}: ` : ''}{issue.category.replace('_', ' ').toUpperCase()}
                      </span>
                      <span className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-bold ${
                        issue.severity === 'high'
                          ? 'bg-red-100 text-red-700'
                          : issue.severity === 'medium'
                          ? 'bg-amber-100 text-amber-700'
                          : 'bg-slate-100 text-slate-600'
                      }`}>
                        {issue.severity}
                      </span>
                    </div>
                    <p className="text-slate-600 leading-snug">{issue.description}</p>
                    <div className="mt-2 text-sky-600 font-medium flex items-center gap-1 text-[11px]">
                      <Sparkles className="w-3 h-3" />
                      Suggested: {issue.suggested_action}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* History Accordion/List */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 mb-3">
              <Clock className="w-4 h-4 text-slate-400" />
              Transformation History
            </h3>
            {history.length === 0 ? (
              <p className="text-xs text-slate-400">No transformations applied yet.</p>
            ) : (
              <div className="space-y-2 max-h-56 overflow-y-auto pr-1 text-xs">
                {history.map((h) => (
                  <div key={h.id} className="p-2 rounded bg-slate-50 border border-slate-200">
                    <div className="flex items-center justify-between font-medium text-slate-700">
                      <span className="capitalize">{h.operation_type.replace(/_/g, ' ')}</span>
                      <span className="text-[10px] text-slate-400">
                        {new Date(h.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      {h.result_summary?.message || 'Executed'}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right 2 Columns: Operation Configuration & Live Diff Preview */}
        <div className="lg:col-span-2 space-y-6">
          {/* Operation Selector Card */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-sm font-bold text-slate-900">Configure Cleaning Operation</h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Operation
                </label>
                <select
                  value={operationType}
                  onChange={(e) => {
                    setOperationType(e.target.value);
                    setPreviewData(null);
                  }}
                  className="w-full text-xs rounded-lg border border-slate-300 p-2 focus:ring-1 focus:ring-sky-500 focus:outline-none"
                >
                  <option value="remove_duplicates">Remove Duplicate Rows</option>
                  <option value="handle_missing_values">Handle Missing Values</option>
                  <option value="trim_whitespace">Trim Whitespace</option>
                  <option value="normalize_case">Normalize Text Casing</option>
                  <option value="convert_data_types">Convert Data Types</option>
                  <option value="remove_columns">Remove Columns</option>
                  <option value="rename_column">Rename Column</option>
                  <option value="filter_rows">Filter Rows</option>
                  <option value="handle_outliers">Handle IQR Outliers</option>
                </select>
              </div>

              {/* Dynamic Inputs based on operation */}
              {['handle_missing_values', 'convert_data_types', 'rename_column', 'filter_rows', 'handle_outliers'].includes(operationType) && (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Target Column
                  </label>
                  <select
                    value={selectedColumn}
                    onChange={(e) => setSelectedColumn(e.target.value)}
                    className="w-full text-xs rounded-lg border border-slate-300 p-2 focus:ring-1 focus:ring-sky-500 focus:outline-none"
                  >
                    {columns.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              )}

              {operationType === 'handle_missing_values' && (
                <>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Strategy</label>
                    <select
                      value={strategy}
                      onChange={(e) => setStrategy(e.target.value)}
                      className="w-full text-xs rounded-lg border border-slate-300 p-2 focus:ring-1 focus:ring-sky-500"
                    >
                      <option value="median">Fill with Median (Numeric)</option>
                      <option value="mean">Fill with Mean (Numeric)</option>
                      <option value="mode">Fill with Mode (Frequent)</option>
                      <option value="constant">Fill with Custom Value</option>
                      <option value="drop">Drop Rows with Missing Values</option>
                    </select>
                  </div>
                  {strategy === 'constant' && (
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">Custom Value</label>
                      <input
                        type="text"
                        value={constantVal}
                        onChange={(e) => setConstantVal(e.target.value)}
                        placeholder="e.g. Unknown or 0"
                        className="w-full text-xs rounded-lg border border-slate-300 p-2 focus:ring-1 focus:ring-sky-500"
                      />
                    </div>
                  )}
                </>
              )}

              {operationType === 'normalize_case' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Casing</label>
                  <select
                    value={casingType}
                    onChange={(e) => setCasingType(e.target.value)}
                    className="w-full text-xs rounded-lg border border-slate-300 p-2 focus:ring-1 focus:ring-sky-500"
                  >
                    <option value="lower">lowercase (e.g. engineering)</option>
                    <option value="upper">UPPERCASE (e.g. ENGINEERING)</option>
                    <option value="title">Title Case (e.g. Engineering)</option>
                  </select>
                </div>
              )}

              {operationType === 'convert_data_types' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Target Type</label>
                  <select
                    value={targetType}
                    onChange={(e) => setTargetType(e.target.value)}
                    className="w-full text-xs rounded-lg border border-slate-300 p-2 focus:ring-1 focus:ring-sky-500"
                  >
                    <option value="integer">Integer</option>
                    <option value="decimal">Decimal</option>
                    <option value="string">String</option>
                    <option value="boolean">Boolean</option>
                    <option value="datetime">Datetime (YYYY-MM-DD)</option>
                  </select>
                </div>
              )}

              {operationType === 'rename_column' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">New Column Name</label>
                  <input
                    type="text"
                    value={renameNew}
                    onChange={(e) => setRenameNew(e.target.value)}
                    placeholder="New name..."
                    className="w-full text-xs rounded-lg border border-slate-300 p-2 focus:ring-1 focus:ring-sky-500"
                  />
                </div>
              )}

              {operationType === 'filter_rows' && (
                <>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Operator</label>
                    <select
                      value={filterOp}
                      onChange={(e) => setFilterOp(e.target.value)}
                      className="w-full text-xs rounded-lg border border-slate-300 p-2 focus:ring-1 focus:ring-sky-500"
                    >
                      <option value="equals">Equals</option>
                      <option value="not_equals">Does Not Equal</option>
                      <option value="contains">Contains (Text)</option>
                      <option value="gt">Greater Than (&gt;)</option>
                      <option value="lt">Less Than (&lt;)</option>
                      <option value="is_missing">Is Missing (Null)</option>
                      <option value="is_not_missing">Is Not Missing</option>
                    </select>
                  </div>
                  {!['is_missing', 'is_not_missing'].includes(filterOp) && (
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">Value</label>
                      <input
                        type="text"
                        value={filterVal}
                        onChange={(e) => setFilterVal(e.target.value)}
                        placeholder="Filter value..."
                        className="w-full text-xs rounded-lg border border-slate-300 p-2 focus:ring-1 focus:ring-sky-500"
                      />
                    </div>
                  )}
                </>
              )}

              {operationType === 'handle_outliers' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Action</label>
                  <select
                    value={outlierAction}
                    onChange={(e) => setOutlierAction(e.target.value)}
                    className="w-full text-xs rounded-lg border border-slate-300 p-2 focus:ring-1 focus:ring-sky-500"
                  >
                    <option value="remove">Remove Outlier Rows</option>
                    <option value="cap">Cap to [Q1-1.5*IQR, Q3+1.5*IQR]</option>
                  </select>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={handlePreview}
                disabled={previewLoading || applyLoading}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition"
              >
                {previewLoading ? 'Calculating Preview...' : '1. Preview Impact'}
              </button>

              <button
                type="button"
                onClick={handleApply}
                disabled={applyLoading}
                className="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold rounded-lg shadow-sm transition flex items-center gap-1.5"
              >
                <Wand2 className="w-3.5 h-3.5" />
                {applyLoading ? 'Applying...' : '2. Apply Transformation & Save Version'}
              </button>
            </div>
          </div>

          {/* Preview Diff Box */}
          {previewData && (
            <div className="bg-white p-6 rounded-xl border border-sky-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Info className="w-4 h-4 text-sky-600" />
                  Expected Transformation Impact
                </h3>
                <span className="text-xs font-semibold text-sky-700 bg-sky-50 px-2 py-0.5 rounded">
                  Safe In-Memory Simulation
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                <div className="p-3 bg-slate-50 rounded-lg">
                  <span className="text-slate-400 font-medium">Expected Rows:</span>
                  <p className="font-bold text-slate-800 text-sm mt-0.5">{previewData.expected_rows}</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <span className="text-slate-400 font-medium">Affected Count:</span>
                  <p className="font-bold text-amber-600 text-sm mt-0.5">{previewData.rows_affected} items</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <span className="text-slate-400 font-medium">Expected Columns:</span>
                  <p className="font-bold text-slate-800 text-sm mt-0.5">{previewData.expected_columns}</p>
                </div>
              </div>

              {previewData.warnings && previewData.warnings.length > 0 && (
                <div className="p-3 bg-amber-50 border border-amber-200 text-amber-800 rounded-lg text-xs">
                  {previewData.warnings.join(' ')}
                </div>
              )}

              {/* Sample Before/After */}
              <div className="space-y-2 pt-2">
                <span className="text-xs font-bold text-slate-700">Sample Row Result Preview:</span>
                <div className="overflow-x-auto border border-slate-200 rounded-lg">
                  <table className="w-full text-left border-collapse text-[11px]">
                    <tbody className="divide-y divide-slate-100">
                      {previewData.sample_after.slice(0, 3).map((row, idx) => (
                        <tr key={idx} className="hover:bg-slate-50">
                          <td className="py-2 px-3 font-semibold text-slate-400">Row {idx + 1}</td>
                          {Object.entries(row).map(([k, v]) => (
                            <td key={k} className="py-2 px-3 whitespace-nowrap">
                              <span className="text-slate-400">{k}: </span>
                              <span className="font-medium text-slate-800">{String(v)}</span>
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
