import React from 'react';
import { Download, FileText, FileCode, Printer, X, Check } from 'lucide-react';
import { apiClient } from '../../api/client';

interface ExportModalProps {
  datasetId: string;
  filename: string;
  onClose: () => void;
}

export const ExportModal: React.FC<ExportModalProps> = ({ datasetId, filename, onClose }) => {
  const download = (format: 'csv' | 'json' | 'unparsed' | 'html') => {
    window.open(apiClient.getExportUrl(datasetId, format), '_blank');
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-lg w-full p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center space-x-2">
            <Download className="w-5 h-5 text-indigo-600" />
            <h3 className="text-sm font-bold text-slate-900">Export Parsed Data &amp; Reports</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 p-1 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-xs text-slate-500">
          Dataset: <span className="font-semibold text-slate-800">{filename}</span>. Select your desired export artifact below:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
          {/* CSV */}
          <button
            onClick={() => download('csv')}
            className="p-3.5 rounded-lg border border-slate-200 hover:border-indigo-400 hover:bg-indigo-50/30 transition-all text-left flex items-start space-x-3 group"
          >
            <div className="p-2 rounded bg-emerald-50 text-emerald-600 group-hover:bg-indigo-100 group-hover:text-indigo-600">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-800">Normalized CSV</div>
              <p className="text-[10px] text-slate-400 mt-0.5">Spreadsheet tabular format with all extracted columns</p>
            </div>
          </button>

          {/* JSON */}
          <button
            onClick={() => download('json')}
            className="p-3.5 rounded-lg border border-slate-200 hover:border-indigo-400 hover:bg-indigo-50/30 transition-all text-left flex items-start space-x-3 group"
          >
            <div className="p-2 rounded bg-blue-50 text-blue-600 group-hover:bg-indigo-100 group-hover:text-indigo-600">
              <FileCode className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-800">Structured JSON</div>
              <p className="text-[10px] text-slate-400 mt-0.5">Full JSON array of normalized log objects</p>
            </div>
          </button>

          {/* HTML Report */}
          <button
            onClick={() => download('html')}
            className="p-3.5 rounded-lg border border-slate-200 hover:border-indigo-400 hover:bg-indigo-50/30 transition-all text-left flex items-start space-x-3 group"
          >
            <div className="p-2 rounded bg-indigo-50 text-indigo-600 group-hover:bg-indigo-100">
              <Printer className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-800">HTML / PDF Report</div>
              <p className="text-[10px] text-slate-400 mt-0.5">Printable summary with KPIs, errors, &amp; evaluations</p>
            </div>
          </button>

          {/* Unparsed Lines */}
          <button
            onClick={() => download('unparsed')}
            className="p-3.5 rounded-lg border border-slate-200 hover:border-amber-400 hover:bg-amber-50/30 transition-all text-left flex items-start space-x-3 group"
          >
            <div className="p-2 rounded bg-amber-50 text-amber-600 group-hover:bg-amber-100">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-800">Unparsed Lines (.txt)</div>
              <p className="text-[10px] text-slate-400 mt-0.5">Raw failed lines with line numbers for debugging</p>
            </div>
          </button>
        </div>

        <div className="flex justify-end pt-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-100 text-slate-700 text-xs font-semibold rounded-lg hover:bg-slate-200"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

