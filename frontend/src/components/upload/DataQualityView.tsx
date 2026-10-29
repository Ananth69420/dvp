import React from 'react';
import {
  FileCheck2,
  AlertTriangle,
  Download,
  Info,
  CheckCircle,
  XCircle,
  Table,
} from 'lucide-react';
import { DataQualityReport, DatasetProfile } from '../../types';
import { apiClient } from '../../api/client';

interface DataQualityViewProps {
  profile: DatasetProfile;
  datasetId: string;
}

export const DataQualityView: React.FC<DataQualityViewProps> = ({ profile, datasetId }) => {
  const dq = profile.data_quality;

  const downloadUnparsed = () => {
    window.open(apiClient.getExportUrl(datasetId, 'unparsed'), '_blank');
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Data Quality &amp; Parser Validation</h2>
            <p className="text-sm text-slate-500 mt-1">
              Deterministic parsing report for <span className="font-semibold text-slate-700">{profile.filename}</span> using <span className="font-mono text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded text-xs">{profile.format}</span>.
            </p>
          </div>
          {dq.unparsed_lines > 0 && (
            <button
              onClick={downloadUnparsed}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-lg bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100 text-xs font-semibold transition-colors shrink-0"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download {dq.unparsed_lines} Unparsed Lines (.txt)</span>
            </button>
          )}
        </div>

        {/* KPI Mini Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Total Lines</span>
            <div className="text-2xl font-bold text-slate-900 mt-1">{dq.total_lines}</div>
          </div>
          <div className="p-4 rounded-lg bg-emerald-50/50 border border-emerald-200">
            <span className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider">Successfully Parsed</span>
            <div className="text-2xl font-bold text-emerald-700 mt-1">{dq.parsed_lines}</div>
          </div>
          <div className="p-4 rounded-lg bg-rose-50/50 border border-rose-200">
            <span className="text-[11px] font-bold text-rose-700 uppercase tracking-wider">Unparsed / Malformed</span>
            <div className="text-2xl font-bold text-rose-700 mt-1">{dq.unparsed_lines}</div>
          </div>
          <div className="p-4 rounded-lg bg-indigo-50/50 border border-indigo-200">
            <span className="text-[11px] font-bold text-indigo-700 uppercase tracking-wider">Success Rate</span>
            <div className="text-2xl font-bold text-indigo-700 mt-1">{dq.success_rate}%</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden flex">
            <div
              className="bg-emerald-500 h-full transition-all duration-500"
              style={{ width: `${dq.success_rate}%` }}
              title={`Parsed: ${dq.success_rate}%`}
            />
            <div
              className="bg-rose-400 h-full transition-all duration-500"
              style={{ width: `${100 - dq.success_rate}%` }}
              title={`Unparsed: ${(100 - dq.success_rate).toFixed(2)}%`}
            />
          </div>
        </div>
      </div>

      {/* Field Presence & Schema Coverage */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <Table className="w-4 h-4 text-indigo-600" />
          Field Extraction &amp; Availability Coverage
        </h3>
        <p className="text-xs text-slate-500 mt-1">
          Missing fields are explicitly cataloged as unavailable rather than fabricated by AI or default fallbacks.
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 mt-4">
          {[
            { key: 'timestamp', label: 'Timestamp (ISO 8601)' },
            { key: 'level', label: 'Log Severity Level' },
            { key: 'service', label: 'Service / Logger' },
            { key: 'message', label: 'Log Message' },
            { key: 'status_code', label: 'HTTP Status Code' },
            { key: 'response_time_ms', label: 'Response Latency' },
            { key: 'source_ip', label: 'Client / Source IP' },
            { key: 'http_method', label: 'HTTP Method' },
            { key: 'request_path', label: 'Request Path / URL' },
          ].map((f) => {
            const count = dq.field_presence[f.key] || 0;
            const isPresent = count > 0;
            const pct = dq.parsed_lines > 0 ? ((count / dq.parsed_lines) * 100).toFixed(0) : '0';

            return (
              <div
                key={f.key}
                className={`p-3 rounded-lg border text-xs ${
                  isPresent
                    ? 'border-emerald-200 bg-emerald-50/30 text-emerald-950'
                    : 'border-slate-200 bg-slate-50 text-slate-400'
                }`}
              >
                <div className="flex items-center justify-between font-semibold">
                  <span>{f.label}</span>
                  {isPresent ? (
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  ) : (
                    <XCircle className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  )}
                </div>
                <div className="mt-1.5 text-[11px] font-mono text-slate-500">
                  {isPresent ? `${count} entries (${pct}%)` : 'Not present in format'}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Malformed & Failed Lines Preview */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-500" />
            Unparsed &amp; Malformed Entries ({dq.sample_failures.length} sampled)
          </h3>
          {dq.sample_failures.length === 0 && (
            <span className="text-xs text-emerald-600 font-semibold flex items-center gap-1">
              <CheckCircle className="w-3.5 h-3.5" /> Clean log (100% parsed)
            </span>
          )}
        </div>

        {dq.sample_failures.length > 0 ? (
          <div className="space-y-2.5">
            {dq.sample_failures.map((fail) => (
              <div
                key={fail.id}
                className="p-3 bg-rose-50/50 border border-rose-200 rounded-lg text-xs font-mono space-y-1"
              >
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-bold text-rose-800">Source Line #{fail.line_number}</span>
                  <span className="text-rose-600 font-sans">{fail.error_details || 'Pattern mismatch'}</span>
                </div>
                <div className="text-slate-700 bg-white p-2 rounded border border-rose-100 overflow-x-auto whitespace-pre">
                  {fail.raw_line}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-500 italic">
            All records in this dataset matched the parser specification perfectly without dropped lines.
          </p>
        )}
      </div>
    </div>
  );
};

