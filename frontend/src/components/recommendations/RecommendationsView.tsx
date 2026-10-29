import React, { useState } from 'react';
import {
  Sparkles,
  Check,
  X,
  Edit2,
  HelpCircle,
  AlertCircle,
  Eye,
  CheckCircle2,
  XCircle,
  Sliders,
  TrendingUp,
} from 'lucide-react';
import { ChartRecommendation, RecommendationEvaluation, EvaluationSummary } from '../../types';
import { apiClient } from '../../api/client';

interface RecommendationsViewProps {
  datasetId: string;
  recommendations: ChartRecommendation[];
  evaluations: EvaluationSummary;
  onEvaluationUpdated: (summary: EvaluationSummary) => void;
  onNavigateToChart: (chartId: string) => void;
}

export const RecommendationsView: React.FC<RecommendationsViewProps> = ({
  datasetId,
  recommendations,
  evaluations,
  onEvaluationUpdated,
  onNavigateToChart,
}) => {
  // Reject reason modal state
  const [rejectModalRec, setRejectModalRec] = useState<ChartRecommendation | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  // Modify modal state
  const [modifyModalRec, setModifyModalRec] = useState<ChartRecommendation | null>(null);
  const [modifiedType, setModifiedType] = useState<string>('bar');
  const [modifyReason, setModifyReason] = useState('');

  const evalMap = new Map(evaluations.evaluations.map((e) => [e.recommendation_id, e]));

  const handleAccept = async (rec: ChartRecommendation) => {
    try {
      const updated = await apiClient.recordEvaluation(datasetId, {
        recommendation_id: rec.id,
        chart_type: rec.chart_type,
        status: 'accepted',
        timestamp: new Date().toISOString(),
      });
      onEvaluationUpdated(updated);
    } catch (err) {
      console.error(err);
    }
  };

  const handleConfirmReject = async () => {
    if (!rejectModalRec) return;
    try {
      const updated = await apiClient.recordEvaluation(datasetId, {
        recommendation_id: rejectModalRec.id,
        chart_type: rejectModalRec.chart_type,
        status: 'rejected',
        user_reason: rejectReason || 'Not required for current analysis goals',
        timestamp: new Date().toISOString(),
      });
      onEvaluationUpdated(updated);
      setRejectModalRec(null);
      setRejectReason('');
    } catch (err) {
      console.error(err);
    }
  };

  const handleConfirmModify = async () => {
    if (!modifyModalRec) return;
    try {
      const updated = await apiClient.recordEvaluation(datasetId, {
        recommendation_id: modifyModalRec.id,
        chart_type: modifyModalRec.chart_type,
        status: 'modified',
        modified_chart_type: modifiedType,
        user_reason: modifyReason || 'Adjusted chart representation',
        timestamp: new Date().toISOString(),
      });
      onEvaluationUpdated(updated);
      setModifyModalRec(null);
      setModifyReason('');
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Evaluation Summary Bar */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-indigo-600" />
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">
                AI-Assisted Visualization Recommendations
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl">
              Recommendations are generated based on available log fields and profiling statistics. The AI recommends schema mappings and analytical questions; actual chart values are deterministically calculated by the backend.
            </p>
          </div>

          {/* Mini Evaluation Tracking Pill */}
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 flex items-center space-x-4 text-xs">
            <div>
              <span className="text-[10px] text-slate-400 font-bold uppercase">Evaluated</span>
              <div className="font-mono font-bold text-slate-800">
                {evaluations.accepted_count + evaluations.rejected_count + evaluations.modified_count} /{' '}
                {recommendations.length}
              </div>
            </div>
            <div className="border-l border-slate-200 pl-3">
              <span className="text-[10px] text-slate-400 font-bold uppercase">Acceptance Rate</span>
              <div className="font-mono font-bold text-indigo-600">
                {evaluations.acceptance_rate}%
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {recommendations.map((rec) => {
          const evalItem = evalMap.get(rec.id);
          const isAccepted = evalItem?.status === 'accepted';
          const isRejected = evalItem?.status === 'rejected';
          const isModified = evalItem?.status === 'modified';

          return (
            <div
              key={rec.id}
              className={`bg-white rounded-xl border p-5 shadow-2xs flex flex-col justify-between transition-all ${
                isAccepted
                  ? 'border-emerald-300 ring-2 ring-emerald-50 bg-emerald-50/10'
                  : isRejected
                  ? 'border-rose-200 opacity-60 bg-slate-50/50'
                  : isModified
                  ? 'border-amber-300 ring-2 ring-amber-50'
                  : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              <div className="space-y-3">
                {/* Header row with chart type and suitability score */}
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-mono text-[11px] font-bold uppercase border border-indigo-200/60">
                      {isModified ? `${evalItem?.modified_chart_type} (Modified)` : rec.chart_type}
                    </span>
                    <h3 className="text-sm font-bold text-slate-900 leading-snug">{rec.title}</h3>
                  </div>

                  <div
                    className="flex items-center space-x-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-slate-100 text-slate-700 shrink-0"
                    title="Heuristic Suitability Score (0.0 - 1.0)"
                  >
                    <TrendingUp className="w-3 h-3 text-indigo-500" />
                    <span>{(rec.suitability_score * 100).toFixed(0)}% Fit</span>
                  </div>
                </div>

                {/* Analytical Question */}
                <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100 text-xs">
                  <div className="flex items-center space-x-1.5 text-slate-500 font-semibold text-[10px] uppercase">
                    <HelpCircle className="w-3 h-3 text-indigo-500" />
                    <span>Target Analytical Question:</span>
                  </div>
                  <p className="text-slate-800 font-medium mt-0.5">{rec.analytical_question}</p>
                </div>

                {/* Reason & Expected Insight */}
                <div className="text-xs space-y-1.5 text-slate-600">
                  <p>
                    <strong className="text-slate-700">Rationale:</strong> {rec.reason}
                  </p>
                  <p>
                    <strong className="text-slate-700">Expected Insight:</strong> {rec.expected_insight}
                  </p>
                  <p className="text-[11px] text-slate-400">
                    <strong>Limitations:</strong> {rec.limitations}
                  </p>
                </div>

                {/* Required Fields */}
                <div className="flex items-center space-x-2 pt-1 text-[11px]">
                  <span className="text-slate-400 font-semibold">Required Fields:</span>
                  <div className="flex flex-wrap gap-1">
                    {rec.required_fields.map((f) => (
                      <span
                        key={f}
                        className="px-1.5 py-0.2 rounded bg-slate-100 font-mono text-slate-600 border border-slate-200 text-[10px]"
                      >
                        {f}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Evaluation State Pill if evaluated */}
                {evalItem && (
                  <div className="pt-1">
                    {isAccepted && (
                      <div className="flex items-center space-x-1.5 text-emerald-700 text-xs font-semibold">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Accepted for interactive visualization dashboard</span>
                      </div>
                    )}
                    {isRejected && (
                      <div className="flex items-center space-x-1.5 text-rose-600 text-xs font-medium">
                        <XCircle className="w-4 h-4" />
                        <span>Rejected: {evalItem.user_reason}</span>
                      </div>
                    )}
                    {isModified && (
                      <div className="flex items-center space-x-1.5 text-amber-700 text-xs font-semibold">
                        <Sliders className="w-4 h-4" />
                        <span>Modified to {evalItem.modified_chart_type}: {evalItem.user_reason}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Action Buttons: Accept / Reject / Modify */}
              <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                <div className="flex items-center space-x-1.5">
                  <button
                    onClick={() => handleAccept(rec)}
                    className={`flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                      isAccepted
                        ? 'bg-emerald-600 text-white'
                        : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                    }`}
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Accept</span>
                  </button>

                  <button
                    onClick={() => setRejectModalRec(rec)}
                    className={`flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                      isRejected
                        ? 'bg-rose-600 text-white'
                        : 'bg-rose-50 text-rose-700 hover:bg-rose-100'
                    }`}
                  >
                    <X className="w-3.5 h-3.5" />
                    <span>Reject</span>
                  </button>

                  <button
                    onClick={() => {
                      setModifyModalRec(rec);
                      setModifiedType(rec.chart_type);
                    }}
                    className={`flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                      isModified
                        ? 'bg-amber-600 text-white'
                        : 'bg-amber-50 text-amber-700 hover:bg-amber-100'
                    }`}
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                    <span>Modify</span>
                  </button>
                </div>

                <button
                  onClick={() => onNavigateToChart(rec.id)}
                  className="flex items-center space-x-1 text-xs text-indigo-600 font-semibold hover:text-indigo-800"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>View Chart</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Reject Modal */}
      {rejectModalRec && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-md w-full p-6 space-y-4">
            <h3 className="text-sm font-bold text-slate-900">
              Record Reason for Rejecting Recommendation
            </h3>
            <p className="text-xs text-slate-500">
              For: <span className="font-semibold text-slate-800">{rejectModalRec.title}</span>
            </p>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-700">Reason / Justification:</label>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="e.g. Redundant metric, cluttering dashboard, not relevant to triage..."
                className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500 min-h-[80px]"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <button
                onClick={() => setRejectModalRec(null)}
                className="px-3 py-1.5 bg-slate-100 text-slate-600 text-xs rounded-lg hover:bg-slate-200"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmReject}
                className="px-4 py-1.5 bg-rose-600 text-white text-xs font-semibold rounded-lg hover:bg-rose-700"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modify Modal */}
      {modifyModalRec && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-md w-full p-6 space-y-4">
            <h3 className="text-sm font-bold text-slate-900">Modify Recommendation Configuration</h3>
            <p className="text-xs text-slate-500">
              Adjust chart type for <span className="font-semibold text-slate-800">{modifyModalRec.title}</span>
            </p>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-700">Select Alternative Chart Type:</label>
                <select
                  value={modifiedType}
                  onChange={(e) => setModifiedType(e.target.value)}
                  className="w-full mt-1 bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs font-medium"
                >
                  <option value="line">Line Chart (Continuous Volume Timeline)</option>
                  <option value="bar">Bar Chart (Categorical Comparison)</option>
                  <option value="stacked_bar">Stacked Bar (Severity Composition)</option>
                  <option value="donut">Donut Chart (Proportional Distribution)</option>
                  <option value="histogram">Histogram (Latency Frequency)</option>
                  <option value="heatmap">Heatmap (Day vs Hour Density)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700">Modification Reason:</label>
                <textarea
                  value={modifyReason}
                  onChange={(e) => setModifyReason(e.target.value)}
                  placeholder="e.g. Prefer bar chart for discrete service comparison..."
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 min-h-[70px] mt-1"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <button
                onClick={() => setModifyModalRec(null)}
                className="px-3 py-1.5 bg-slate-100 text-slate-600 text-xs rounded-lg hover:bg-slate-200"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmModify}
                className="px-4 py-1.5 bg-amber-600 text-white text-xs font-semibold rounded-lg hover:bg-amber-700"
              >
                Save Modification
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

