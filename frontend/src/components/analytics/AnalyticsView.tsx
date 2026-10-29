import React from 'react';
import {
  AlertOctagon,
  AlertTriangle,
  Info,
  Bug,
  Activity,
  Layers,
  Zap,
  Clock,
  Flame,
  CheckCircle,
} from 'lucide-react';
import { LogAnalytics } from '../../types';

interface AnalyticsViewProps {
  analytics: LogAnalytics;
}

export const AnalyticsView: React.FC<AnalyticsViewProps> = ({ analytics }) => {
  return (
    <div className="space-y-6">
      {/* KPI Highlights Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Total Lines</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">{analytics.total_lines}</div>
          <div className="text-[10px] text-emerald-600 font-semibold mt-0.5">
            {analytics.success_rate}% parsed
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-rose-200 bg-rose-50/20 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-rose-600 uppercase tracking-wider">Errors</span>
            <AlertOctagon className="w-4 h-4 text-rose-500" />
          </div>
          <div className="text-2xl font-bold text-rose-700 mt-1">{analytics.error_count}</div>
          <div className="text-[10px] text-rose-500 font-medium mt-0.5">
            {analytics.critical_count > 0 ? `${analytics.critical_count} critical` : 'Actionable faults'}
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-amber-200 bg-amber-50/20 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-amber-700 uppercase tracking-wider">Warnings</span>
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-amber-700 mt-1">{analytics.warning_count}</div>
          <div className="text-[10px] text-amber-600 font-medium mt-0.5">Subsystem alerts</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-blue-200 bg-blue-50/20 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-blue-700 uppercase tracking-wider">Info</span>
            <Info className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-bold text-blue-700 mt-1">{analytics.info_count}</div>
          <div className="text-[10px] text-blue-600 font-medium mt-0.5">Normal traffic</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Services</span>
            <Layers className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            {analytics.distinct_services_count}
          </div>
          <div className="text-[10px] text-slate-500 truncate mt-0.5" title={analytics.most_active_service || ''}>
            Top: {analytics.most_active_service || 'N/A'}
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Latency</span>
            <Clock className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            {analytics.response_time_stats ? `${analytics.response_time_stats.avg_ms}ms` : 'N/A'}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            {analytics.response_time_stats
              ? `p95: ${analytics.response_time_stats.p95_ms}ms`
              : 'No latency field'}
          </div>
        </div>
      </div>

      {/* Potential Statistical Anomalies Banner */}
      {analytics.anomalies.length > 0 && (
        <div className="bg-amber-50/70 border border-amber-300/80 rounded-xl p-5 shadow-2xs space-y-3">
          <div className="flex items-center space-x-2">
            <Flame className="w-5 h-5 text-amber-600 shrink-0" />
            <h3 className="text-sm font-bold text-amber-900">
              Potential Statistical Anomalies Detected ({analytics.anomalies.length})
            </h3>
            <span className="text-[10px] bg-amber-200/70 text-amber-900 font-semibold px-2 py-0.5 rounded-full">
              Automated Heuristic Rules
            </span>
          </div>
          <p className="text-xs text-amber-800 leading-relaxed">
            Note: These events deviate statistically from local baseline averages (e.g. &gt; 2 standard deviations) and are labeled as <strong>potential anomalies rather than confirmed incidents</strong>.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 pt-1">
            {analytics.anomalies.map((anom) => (
              <div
                key={anom.id}
                className="bg-white p-3 rounded-lg border border-amber-200 text-xs space-y-1 shadow-2xs"
              >
                <div className="flex items-center justify-between font-bold">
                  <span className="text-amber-950">{anom.title}</span>
                  <span
                    className={`text-[10px] px-1.5 py-0.2 rounded font-semibold uppercase ${
                      anom.severity === 'high'
                        ? 'bg-rose-100 text-rose-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {anom.severity} priority
                  </span>
                </div>
                <p className="text-slate-600 text-[11px]">{anom.description}</p>
                {anom.timestamp_interval && (
                  <div className="text-[10px] text-slate-400 font-mono">
                    Time interval: {anom.timestamp_interval}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Two Column Section: Top Errors & Services Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Recurring Errors */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <AlertOctagon className="w-4 h-4 text-rose-500" />
              Top Recurring Error Signatures
            </h3>
            <span className="text-xs text-slate-400">Ranked by count</span>
          </div>

          {analytics.top_errors.length === 0 ? (
            <p className="text-xs text-slate-400 italic py-6 text-center">No error records found in dataset.</p>
          ) : (
            <div className="space-y-3">
              {analytics.top_errors.slice(0, 7).map((err, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1.5"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-mono text-slate-900 font-semibold break-words max-w-[80%]">
                      {err.message}
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 font-bold text-[11px] shrink-0">
                      {err.count} ({err.percentage}%)
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-1.5 text-[10px] text-slate-500">
                    <span className="font-semibold">Services:</span>
                    {err.services.map((s) => (
                      <span key={s} className="px-1.5 py-0.2 bg-white rounded border border-slate-200 text-slate-700">
                        {s}
                      </span>
                    ))}
                    {err.first_seen && (
                      <span className="ml-auto font-mono text-[10px] text-slate-400">
                        First: {err.first_seen.slice(11, 19)}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Service Activity Breakdown */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-600" />
              Service Error &amp; Activity Breakdown
            </h3>
            <span className="text-xs text-slate-400">Grouped by service tag</span>
          </div>

          {analytics.service_stats.length === 0 ? (
            <p className="text-xs text-slate-400 italic py-6 text-center">No service labels extracted.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 font-semibold bg-slate-50/50">
                    <th className="py-2 px-3">Service</th>
                    <th className="py-2 px-3 text-right">Total</th>
                    <th className="py-2 px-3 text-right">Errors</th>
                    <th className="py-2 px-3 text-right">Warnings</th>
                    <th className="py-2 px-3 text-right">Failure Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {analytics.service_stats.map((s) => (
                    <tr key={s.service} className="hover:bg-slate-50">
                      <td className="py-2 px-3 font-semibold text-slate-800">{s.service}</td>
                      <td className="py-2 px-3 text-right font-mono text-slate-600">{s.total_entries}</td>
                      <td className="py-2 px-3 text-right font-mono font-bold text-rose-600">{s.error_count}</td>
                      <td className="py-2 px-3 text-right font-mono text-amber-600">{s.warning_count}</td>
                      <td className="py-2 px-3 text-right font-mono">
                        <span
                          className={`px-1.5 py-0.5 rounded font-bold ${
                            s.error_rate > 30
                              ? 'bg-rose-100 text-rose-800'
                              : s.error_rate > 10
                              ? 'bg-amber-100 text-amber-800'
                              : 'text-slate-600'
                          }`}
                        >
                          {s.error_rate}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Response Time Breakdown if available */}
          {analytics.response_time_stats && (
            <div className="pt-4 border-t border-slate-100">
              <h4 className="text-xs font-bold text-slate-800 mb-2 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-slate-500" />
                Response Latency Percentiles (ms)
              </h4>
              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                <div className="p-2 bg-slate-50 rounded border border-slate-200">
                  <div className="text-[10px] text-slate-400 font-bold uppercase">Average</div>
                  <div className="font-mono font-bold text-slate-800">{analytics.response_time_stats.avg_ms}ms</div>
                </div>
                <div className="p-2 bg-slate-50 rounded border border-slate-200">
                  <div className="text-[10px] text-slate-400 font-bold uppercase">Median</div>
                  <div className="font-mono font-bold text-slate-800">{analytics.response_time_stats.median_ms}ms</div>
                </div>
                <div className="p-2 bg-slate-50 rounded border border-slate-200">
                  <div className="text-[10px] text-slate-400 font-bold uppercase">p95 Tail</div>
                  <div className="font-mono font-bold text-amber-700">{analytics.response_time_stats.p95_ms}ms</div>
                </div>
                <div className="p-2 bg-slate-50 rounded border border-slate-200">
                  <div className="text-[10px] text-slate-400 font-bold uppercase">p99 Outlier</div>
                  <div className="font-mono font-bold text-rose-700">{analytics.response_time_stats.p99_ms}ms</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

