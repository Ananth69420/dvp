import React, { useState } from 'react';
import {
  HelpCircle,
  Search,
  Sparkles,
  ShieldCheck,
  Lightbulb,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Database,
  Flame,
} from 'lucide-react';
import { InvestigateResponse } from '../../types';
import { apiClient } from '../../api/client';

interface InvestigationViewProps {
  datasetId: string;
}

const PRESET_QUERIES = [
  'What should I inspect first?',
  'What are the most common errors?',
  'Which service generates the most errors?',
  'When did error activity increase?',
  'Which HTTP endpoints have the highest failure rate?',
  'Are there unusually slow responses?',
];

export const InvestigationView: React.FC<InvestigationViewProps> = ({ datasetId }) => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<InvestigateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runInvestigation = async (qText: string) => {
    if (!qText.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await apiClient.investigate(datasetId, qText);
      setResponse(res);
    } catch (err: any) {
      setError(err.message || 'Investigation query failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    runInvestigation(query);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Search Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs space-y-4">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-5 h-5 text-indigo-600" />
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            AI-Assisted Operational SRE Investigation
          </h2>
        </div>
        <p className="text-xs text-slate-500 leading-relaxed">
          Ask questions about failure cascades, service bottlenecks, latency outliers, and error timing. The backend deterministically calculates factual metrics from parsed log records; the AI structures empirical evidence vs working hypotheses.
        </p>

        {/* Query Input */}
        <form onSubmit={handleFormSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. Which service generates the most errors, and when did errors spike?"
              className="w-full pl-9 pr-4 py-2.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
            />
          </div>
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg text-xs font-semibold hover:bg-indigo-700 disabled:opacity-40 transition-colors shadow-2xs shrink-0 flex items-center gap-1.5"
          >
            <span>{isLoading ? 'Analyzing...' : 'Investigate'}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>

        {/* Suggested Quick Queries */}
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Suggested SRE Questions:
          </span>
          <div className="flex flex-wrap gap-1.5 mt-2">
            {PRESET_QUERIES.map((preset) => (
              <button
                key={preset}
                onClick={() => {
                  setQuery(preset);
                  runInvestigation(preset);
                }}
                disabled={isLoading}
                className="px-2.5 py-1 rounded-md bg-slate-50 border border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/50 text-[11px] text-slate-600 hover:text-indigo-700 transition-all text-left"
              >
                {preset}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Investigation Results Section */}
      {response && (
        <div className="space-y-4">
          {/* Query Title */}
          <div className="bg-slate-900 text-white p-4 rounded-xl shadow-xs flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Database className="w-4 h-4 text-indigo-400" />
              <span className="text-xs text-slate-300">Investigation Query:</span>
              <span className="text-xs font-bold text-white">"{response.query}"</span>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-emerald-400 font-mono border border-slate-700">
              Evidence Verified
            </span>
          </div>

          {/* Section 1: Observed Factual Findings */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs space-y-3">
            <div className="flex items-center space-x-2 pb-2 border-b border-slate-100">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
              <h3 className="text-sm font-bold text-slate-900">
                1. Observed Empirical Findings (Calculated from Data)
              </h3>
            </div>
            <p className="text-xs text-slate-500">
              These findings reflect actual counts, timestamps, and percentages verified by the backend analytics engine:
            </p>
            <ul className="space-y-2 mt-2">
              {response.factual_findings.map((fact, idx) => (
                <li
                  key={idx}
                  className="flex items-start space-x-2.5 text-xs text-slate-800 bg-slate-50 p-2.5 rounded-lg border border-slate-100"
                >
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span className="font-medium leading-relaxed">{fact}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Section 2: Hypotheses & Diagnostic Interpretations */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs space-y-3">
            <div className="flex items-center space-x-2 pb-2 border-b border-slate-100">
              <Lightbulb className="w-5 h-5 text-amber-500" />
              <h3 className="text-sm font-bold text-slate-900">
                2. Working Hypotheses &amp; Potential Root Causes
              </h3>
            </div>
            <p className="text-xs text-slate-500">
              Carefully distinguished from observed facts. These are hypotheses consistent with the data:
            </p>
            <ul className="space-y-2 mt-2">
              {response.hypotheses.map((hypo, idx) => (
                <li
                  key={idx}
                  className="flex items-start space-x-2.5 text-xs text-slate-800 bg-amber-50/40 p-2.5 rounded-lg border border-amber-200/60"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0 mt-1.5" />
                  <span className="leading-relaxed">{hypo}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Section 3: Recommended Triage & Next Action Items */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs space-y-3">
            <div className="flex items-center space-x-2 pb-2 border-b border-slate-100">
              <Flame className="w-5 h-5 text-indigo-600" />
              <h3 className="text-sm font-bold text-slate-900">
                3. Recommended Engineering Action Items
              </h3>
            </div>
            <ul className="space-y-2 mt-2">
              {response.recommended_checks.map((chk, idx) => (
                <li
                  key={idx}
                  className="flex items-start space-x-2.5 text-xs text-slate-800 bg-indigo-50/30 p-2.5 rounded-lg border border-indigo-100"
                >
                  <ArrowRight className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                  <span className="font-semibold text-slate-900">{chk}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

