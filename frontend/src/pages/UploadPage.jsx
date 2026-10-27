import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { datasetService } from '../services/datasetService';
import { UploadCloud, FileText, AlertCircle, CheckCircle2, ArrowRight } from 'lucide-react';

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  };

  const handleFileSelected = (selectedFile) => {
    setError(null);
    const ext = selectedFile.name.split('.').pop().toLowerCase();
    if (!['csv', 'xlsx'].includes(ext)) {
      setError('Please select a valid CSV or XLSX file.');
      return;
    }
    if (selectedFile.size > 50 * 1024 * 1024) {
      setError('File size exceeds the 50MB limit.');
      return;
    }
    setFile(selectedFile);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please choose a file to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      setUploading(true);
      setError(null);
      const res = await datasetService.uploadDataset(formData);
      const datasetId = res.data.id;
      navigate(`/datasets/${datasetId}`);
    } catch (err) {
      const msg = err.response?.data?.detail || 'An error occurred during upload.';
      setError(msg);
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Upload Dataset</h1>
        <p className="text-sm text-slate-500 mt-1">
          Import your CSV or Excel dataset to begin quality profiling, cleaning, and interactive visualization.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-8 text-center transition ${
            dragActive
              ? 'border-sky-500 bg-sky-50/50'
              : 'border-slate-300 hover:border-slate-400 bg-white'
          }`}
        >
          <input
            type="file"
            id="file-upload"
            className="hidden"
            accept=".csv, .xlsx"
            onChange={handleChange}
          />
          <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
            <div className="w-14 h-14 bg-sky-50 text-sky-600 rounded-full flex items-center justify-center mb-3">
              <UploadCloud className="w-7 h-7" />
            </div>
            <p className="text-sm font-semibold text-slate-800">
              Click to select or drag and drop your file here
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Supports CSV, XLSX up to 50MB
            </p>
          </label>
        </div>

        {file && (
          <div className="bg-white p-4 rounded-xl border border-slate-200 flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center text-slate-600">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-800">{file.name}</p>
                <p className="text-xs text-slate-400">
                  {(file.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setFile(null)}
              className="text-xs text-red-600 hover:text-red-800 font-medium"
            >
              Remove
            </button>
          </div>
        )}

        <button
          type="submit"
          disabled={!file || uploading}
          className={`w-full py-2.5 px-4 rounded-lg font-medium text-sm flex items-center justify-center gap-2 transition ${
            !file || uploading
              ? 'bg-slate-300 text-slate-500 cursor-not-allowed'
              : 'bg-sky-600 hover:bg-sky-700 text-white shadow-sm'
          }`}
        >
          {uploading ? 'Processing Dataset...' : 'Upload and Inspect Data'}
          {!uploading && <ArrowRight className="w-4 h-4" />}
        </button>
      </form>
    </div>
  );
}
