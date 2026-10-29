import React from 'react';
import { BookOpen, CheckCircle, ShieldCheck, Cpu, Database, BarChart2, X } from 'lucide-react';

interface ProjectSynopsisModalProps {
  onClose: () => void;
}

export const ProjectSynopsisModal: React.FC<ProjectSynopsisModalProps> = ({ onClose }) => {
  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-3xl w-full p-6 space-y-5 max-h-[85vh] overflow-y-auto">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center space-x-2">
            <BookOpen className="w-5 h-5 text-indigo-600" />
            <div>
              <h3 className="text-base font-bold text-slate-900">
                Data Visualization Project (DVP) Synopsis
              </h3>
              <p className="text-xs text-slate-500">
                Log File Parser and AI-Assisted Log Visualization System
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 p-1 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Executive Summary */}
        <div className="bg-indigo-50/50 p-4 rounded-lg border border-indigo-100 text-xs text-slate-700 leading-relaxed space-y-1.5">
          <p className="font-semibold text-indigo-950">Project Synopsis &amp; Problem Statement:</p>
          <p>
            In modern distributed microservices and cloud infrastructures, raw log files are high-volume, semi-structured, and diverse in syntax. Engineers often struggle to quickly ascertain failure cascades, latency outliers, and service degradation. This project builds a specialized <strong>Log File Parser and AI-Assisted Log Visualization System</strong> that transitions from raw unstructured log streams into normalized data, high-performance Pandas analytics, and AI-recommended interactive visual charts.
          </p>
        </div>

        {/* 3 Pillars */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50 space-y-1.5">
            <div className="flex items-center space-x-1.5 font-bold text-slate-900">
              <Database className="w-4 h-4 text-emerald-600" />
              <span>1. Modular Parser Engine</span>
            </div>
            <p className="text-slate-500 text-[11px] leading-relaxed">
              Deterministic regex and schema normalizers for Microservices, Python tracebacks, Nginx/Apache CLF/Combined logs, JSON Lines, and CSV. Preserves original lines and tracks malformed rows.
            </p>
          </div>

          <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50 space-y-1.5">
            <div className="flex items-center space-x-1.5 font-bold text-slate-900">
              <BarChart2 className="w-4 h-4 text-indigo-600" />
              <span>2. Verified Analytics Engine</span>
            </div>
            <p className="text-slate-500 text-[11px] leading-relaxed">
              Pandas and NumPy compute exact error rates, latency percentiles (avg, median, p90, p95, p99), time volume series, and statistical anomaly detection (z-score error surges and activity bursts).
            </p>
          </div>

          <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50 space-y-1.5">
            <div className="flex items-center space-x-1.5 font-bold text-slate-900">
              <Cpu className="w-4 h-4 text-amber-600" />
              <span>3. AI Recommendation &amp; SRE</span>
            </div>
            <p className="text-slate-500 text-[11px] leading-relaxed">
              Recommends optimal visualizations with analytical questions and suitability scores. Recommends metadata only—backend aggregates all chart values. Tracks user evaluation decisions.
            </p>
          </div>
        </div>

        {/* Core Principles & Constraints */}
        <div className="space-y-2 text-xs">
          <h4 className="font-bold text-slate-900">Design Constraints &amp; Engineering Rigor:</h4>
          <ul className="space-y-1 text-slate-600 list-disc list-inside">
            <li><strong>No Fabricated Data:</strong> Missing fields remain unavailable rather than hallucinated or imputed.</li>
            <li><strong>AI Safety &amp; Untrusted Inputs:</strong> Log contents are treated as untrusted data strings. AI only recommends visualization structures and analytical questions.</li>
            <li><strong>Deterministic Rule Fallback:</strong> The entire application operates 100% locally and offline without an OpenAI API key.</li>
            <li><strong>Evaluation Auditability:</strong> Acceptance rate measures user decisions and workflow fit, not algorithmic accuracy.</li>
          </ul>
        </div>

        <div className="flex justify-end pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-semibold hover:bg-slate-800"
          >
            Close Synopsis
          </button>
        </div>
      </div>
    </div>
  );
};

