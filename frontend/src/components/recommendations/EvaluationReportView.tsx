import React from 'react';
import {
  ClipboardCheck,
  CheckCircle2,
  XCircle,
  Sliders,
  TrendingUp,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';
import { EvaluationSummary, ChartRecommendation } from '../../types';

interface EvaluationReportViewProps {
  evaluations: EvaluationSummary;
  recommendations: ChartRecommendation[];
}

export const EvaluationReportView: React.FC<EvaluationReportViewProps> = ({
  evaluations,
  recommendations,
}) => {
  const evalMap = new Map(evaluations.evaluations.map((e) => [e.recommendation_id, e]));

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Overview Banner */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs space-y-4">
        <div className="flex items-center space-x-2">
          <ClipboardCheck className="w-5 h-5 text-indigo-600" />
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            AI Recommendation Evaluation &amp; User Decisions Report
          </h2>
        </div>
        <p className="text-xs text-slate-500 leading-relaxed max-w-3xl">
          This audit tracking measures human-in-the-loop decisions on AI-recommended visualizations.
          <strong className="text-slate-700"> Important Notice:</strong> The acceptance rate reflects user decisions and task-specific alignment; it is not a direct measure of AI algorithmic accuracy.
        </p>

        {/* Evaluation Metrics Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2">
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              Total Proposed
            </span>
            <div className="text-2xl font-bold text-slate-900 mt-1">
              {evaluations.total_recommendations}
            </div>
          </div>

          <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200">
            <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider">
              Accepted
            </span>
            <div className="text-2xl font-bold text-emerald-700 mt-1">
              {evaluations.accepted_count}
            </div>
          </div>

          <div className="p-4 rounded-lg bg-rose-50 border border-rose-200">
            <span className="text-[10px] font-bold text-rose-700 uppercase tracking-wider">
              Rejected
            </span>
            <div className="text-2xl font-bold text-rose-700 mt-1">
              {evaluations.rejected_count}
            </div>
          </div>

          <div className="p-4 rounded-lg bg-amber-50 border border-amber-200">
            <span className="text-[10px] font-bold text-amber-700 uppercase tracking-wider">
              Modified
            </span>
            <div className="text-2xl font-bold text-amber-700 mt-1">
              {evaluations.modified_count}
            </div>
          </div>

          <div className="p-4 rounded-lg bg-indigo-50 border border-indigo-200">
            <span className="text-[10px] font-bold text-indigo-700 uppercase tracking-wider">
              Acceptance Rate
            </span>
            <div className="text-2xl font-bold text-indigo-700 mt-1">
              {evaluations.acceptance_rate}%
            </div>
          </div>
        </div>

        {/* Decision Breakdown Progress Bar */}
        <div className="pt-2">
          <div className="flex justify-between text-[11px] font-medium text-slate-500 mb-1">
            <span>Decision Distribution</span>
            <span>
              {evaluations.accepted_count} Accepted / {evaluations.rejected_count} Rejected /{' '}
              {evaluations.modified_count} Modified
            </span>
          </div>
          <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden flex">
            {evaluations.total_recommendations > 0 ? (
              <>
                <div
                  className="bg-emerald-500 h-full"
                  style={{
                    width: `${(evaluations.accepted_count / evaluations.total_recommendations) * 100}%`,
                  }}
                  title="Accepted"
                />
                <div
                  className="bg-amber-400 h-full"
                  style={{
                    width: `${(evaluations.modified_count / evaluations.total_recommendations) * 100}%`,
                  }}
                  title="Modified"
                />
                <div
                  className="bg-rose-400 h-full"
                  style={{
                    width: `${(evaluations.rejected_count / evaluations.total_recommendations) * 100}%`,
                  }}
                  title="Rejected"
                />
              </>
            ) : (
              <div className="bg-slate-200 h-full w-full" />
            )}
          </div>
        </div>
      </div>

      {/* Comparison Table: Proposed vs User Final Selection */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs space-y-4">
        <h3 className="text-sm font-bold text-slate-900">
          Comparison: AI Proposed Recommendations vs. Human Selections
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 font-semibold bg-slate-50/50">
                <th className="py-2.5 px-3">Recommendation Title</th>
                <th className="py-2.5 px-3">Proposed Chart</th>
                <th className="py-2.5 px-3">Fit Score</th>
                <th className="py-2.5 px-3">User Action</th>
                <th className="py-2.5 px-3">Final Effective Chart</th>
                <th className="py-2.5 px-3">Recorded Justification</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
              {recommendations.map((rec) => {
                const ev = evalMap.get(rec.id);
                const status = ev?.status || 'pending';

                return (
                  <tr key={rec.id} className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 font-sans font-semibold text-slate-800">
                      {rec.title}
                    </td>
                    <td className="py-2.5 px-3 text-slate-600 font-bold uppercase">
                      {rec.chart_type}
                    </td>
                    <td className="py-2.5 px-3 text-slate-500">
                      {(rec.suitability_score * 100).toFixed(0)}%
                    </td>
                    <td className="py-2.5 px-3 font-sans">
                      {status === 'accepted' ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                          <CheckCircle2 className="w-3 h-3 mr-1" /> Accepted
                        </span>
                      ) : status === 'rejected' ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800">
                          <XCircle className="w-3 h-3 mr-1" /> Rejected
                        </span>
                      ) : status === 'modified' ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">
                          <Sliders className="w-3 h-3 mr-1" /> Modified
                        </span>
                      ) : (
                        <span className="text-slate-400 italic">Pending decision</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 uppercase font-bold text-slate-800">
                      {status === 'modified'
                        ? ev?.modified_chart_type
                        : status === 'accepted'
                        ? rec.chart_type
                        : '-'}
                    </td>
                    <td className="py-2.5 px-3 font-sans text-slate-600 max-w-xs truncate">
                      {ev?.user_reason || (status === 'accepted' ? 'Accepted as proposed' : '-')}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

