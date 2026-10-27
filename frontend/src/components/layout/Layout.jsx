import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { 
  Database, 
  UploadCloud, 
  Wand2, 
  BarChart2, 
  Download, 
  Home, 
  Layers 
} from 'lucide-react';

export default function Layout({ children, currentDataset }) {
  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col flex-shrink-0 border-r border-slate-800">
        <div className="p-5 flex items-center gap-3 border-b border-slate-800">
          <div className="w-9 h-9 bg-sky-500 text-white rounded-lg flex items-center justify-center font-bold text-lg shadow-sm">
            DL
          </div>
          <div>
            <h1 className="font-bold text-white text-base leading-tight tracking-wide">DataLens</h1>
            <p className="text-xs text-slate-400">Data Analytics Studio</p>
          </div>
        </div>

        <nav className="p-4 flex-1 space-y-1">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-3 mb-2">Main</div>
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive ? 'bg-sky-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            <Home className="w-4 h-4" />
            Dashboard
          </NavLink>

          <NavLink
            to="/upload"
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive ? 'bg-sky-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            <UploadCloud className="w-4 h-4" />
            Upload Dataset
          </NavLink>

          {currentDataset && (
            <>
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-3 mt-6 mb-2">
                Active Dataset
              </div>
              <div className="px-3 py-2 mb-2 bg-slate-800/60 rounded-lg border border-slate-700/50">
                <p className="text-xs font-semibold text-sky-400 truncate" title={currentDataset.original_filename}>
                  {currentDataset.original_filename}
                </p>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  {currentDataset.row_count?.toLocaleString()} rows • {currentDataset.column_count} cols
                </p>
              </div>

              <NavLink
                to={`/datasets/${currentDataset.id}`}
                end
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-sky-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`
                }
              >
                <Database className="w-4 h-4" />
                Data & Profile
              </NavLink>

              <NavLink
                to={`/datasets/${currentDataset.id}/clean`}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-sky-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`
                }
              >
                <Wand2 className="w-4 h-4" />
                Cleaning Studio
              </NavLink>

              <NavLink
                to={`/datasets/${currentDataset.id}/visualize`}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-sky-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`
                }
              >
                <BarChart2 className="w-4 h-4" />
                Visualization
              </NavLink>

              <NavLink
                to={`/datasets/${currentDataset.id}/export`}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-sky-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`
                }
              >
                <Download className="w-4 h-4" />
                Export
              </NavLink>
            </>
          )}
        </nav>

        <div className="p-4 border-t border-slate-800 text-xs text-slate-400 flex items-center justify-between">
          <span>Engine v1.0 (Modular)</span>
          <span className="w-2 h-2 rounded-full bg-emerald-400" title="Connected"></span>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Navbar */}
        <header className="h-14 bg-white border-b border-slate-200 px-6 flex items-center justify-between shadow-sm z-10">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Link to="/" className="hover:text-slate-800">Home</Link>
            {currentDataset && (
              <>
                <span>/</span>
                <span className="font-medium text-slate-800 truncate max-w-xs">{currentDataset.original_filename}</span>
              </>
            )}
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/upload"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-sky-600 text-white hover:bg-sky-700 transition"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              New Dataset
            </Link>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6 bg-slate-50">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
