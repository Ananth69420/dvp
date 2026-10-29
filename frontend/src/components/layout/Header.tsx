import React from 'react';
import { Activity, ShieldCheck, Download, Sparkles, Database } from 'lucide-react';
import { DatasetProfile } from '../../types';

interface HeaderProps {
  profile: DatasetProfile | null;
  onOpenExport: () => void;
  onOpenSynopsis: () => void;
  isBackendHealthy: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  profile,
  onOpenExport,
  onOpenSynopsis,
  isBackendHealthy,
}) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 px-6 py-3.5 flex items-center justify-between shadow-xs">
      <div className="flex items-center space-x-3">
        <div className="h-9 w-9 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-sm">
          <Activity className="h-5 w-5" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-lg font-bold text-slate-900 tracking-tight">LogLens AI</h1>
            <span className="text-xs font-semibold px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded-full border border-indigo-200/60 flex items-center gap-1">
              <Sparkles className="w-3 h-3" /> DVP AI-Assisted
            </span>
          </div>
          <p className="text-xs text-slate-500">Log File Parser &amp; Visual Analytics System</p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {profile ? (
          <div className="hidden md:flex items-center space-x-3 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 text-xs">
            <div className="flex items-center space-x-1.5">
              <Database className="w-3.5 h-3.5 text-slate-500" />
              <span className="font-medium text-slate-700 max-w-[160px] truncate" title={profile.filename}>
                {profile.filename}
              </span>
            </div>
            <span className="text-slate-300">|</span>
            <span className="px-2 py-0.5 rounded bg-white text-slate-600 font-mono text-[11px] border border-slate-200">
              {profile.format}
            </span>
            <span className="text-slate-300">|</span>
            <span className="text-emerald-700 font-semibold">
              {profile.data_quality.success_rate}% parsed
            </span>
          </div>
        ) : (
          <span className="text-xs text-slate-400 italic">No dataset loaded</span>
        )}

        <div className="flex items-center space-x-1 text-xs">
          <span
            className={`w-2 h-2 rounded-full ${
              isBackendHealthy ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
            }`}
          />
          <span className="text-slate-500 text-[11px] font-medium">
            {isBackendHealthy ? 'Engine Online' : 'Engine Offline'}
          </span>
        </div>

        <button
          onClick={onOpenSynopsis}
          className="text-xs font-medium text-slate-600 hover:text-indigo-600 px-3 py-1.5 rounded-md hover:bg-slate-100 transition-colors"
        >
          Project Synopsis
        </button>

        {profile && (
          <button
            onClick={onOpenExport}
            className="flex items-center space-x-1.5 bg-slate-900 text-white hover:bg-slate-800 text-xs font-medium px-3.5 py-1.5 rounded-lg shadow-xs transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export &amp; Report</span>
          </button>
        )}
      </div>
    </header>
  );
};

