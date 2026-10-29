import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  Maximize2,
  X,
  AlertOctagon,
  AlertTriangle,
  Info,
  Bug,
  Globe,
  Clock,
  Layers,
} from 'lucide-react';
import { LogEntry, PaginatedEntries } from '../../types';
import { apiClient } from '../../api/client';

interface LogExplorerProps {
  datasetId: string;
  availableServices: string[];
}

export const LogExplorer: React.FC<LogExplorerProps> = ({ datasetId, availableServices }) => {
  const [entries, setEntries] = useState<LogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [isLoading, setIsLoading] = useState(false);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLevel, setSelectedLevel] = useState('ALL');
  const [selectedService, setSelectedService] = useState('ALL');
  const [selectedStatusCode, setSelectedStatusCode] = useState<string>('ALL');
  const [parseStatusFilter, setParseStatusFilter] = useState<'parsed' | 'malformed' | 'all'>('parsed');
  const [sortBy, setSortBy] = useState('line_number');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  // Selected entry for modal view
  const [inspectEntry, setInspectEntry] = useState<LogEntry | null>(null);

  const fetchEntries = async () => {
    setIsLoading(true);
    try {
      const data = await apiClient.getEntries(datasetId, {
        search: searchTerm || undefined,
        level: selectedLevel !== 'ALL' ? selectedLevel : undefined,
        service: selectedService !== 'ALL' ? selectedService : undefined,
        statusCode: selectedStatusCode !== 'ALL' ? parseInt(selectedStatusCode, 10) : undefined,
        parseStatus: parseStatusFilter,
        page,
        pageSize,
        sortBy,
        sortDir,
      });
      setEntries(data.entries);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEntries();
  }, [datasetId, page, pageSize, selectedLevel, selectedService, selectedStatusCode, parseStatusFilter, sortBy, sortDir]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchEntries();
  };

  const handleResetFilters = () => {
    setSearchTerm('');
    setSelectedLevel('ALL');
    setSelectedService('ALL');
    setSelectedStatusCode('ALL');
    setParseStatusFilter('parsed');
    setSortBy('line_number');
    setSortDir('asc');
    setPage(1);
  };

  const getLevelBadge = (level: string | null) => {
    switch (level?.toUpperCase()) {
      case 'CRITICAL':
      case 'ERROR':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-rose-100 text-rose-700 border border-rose-200">
            <AlertOctagon className="w-3 h-3 mr-1" /> {level}
          </span>
        );
      case 'WARN':
      case 'WARNING':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
            <AlertTriangle className="w-3 h-3 mr-1" /> {level}
          </span>
        );
      case 'INFO':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-blue-50 text-blue-700 border border-blue-200">
            <Info className="w-3 h-3 mr-1" /> INFO
          </span>
        );
      case 'DEBUG':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-600 border border-slate-200">
            <Bug className="w-3 h-3 mr-1" /> DEBUG
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-500">
            {level || '-'}
          </span>
        );
    }
  };

  return (
    <div className="space-y-4">
      {/* Search and Filters Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-2.5">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search keyword in message or raw log..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold hover:bg-indigo-700 transition-colors shadow-2xs"
          >
            Apply Search
          </button>
          <button
            type="button"
            onClick={handleResetFilters}
            className="px-3 py-2 bg-slate-100 text-slate-600 rounded-lg text-xs font-medium hover:bg-slate-200 transition-colors flex items-center gap-1.5"
            title="Reset All Filters"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
        </form>

        <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-100 text-xs">
          {/* Status Tab (Parsed vs Malformed) */}
          <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200">
            <button
              onClick={() => {
                setParseStatusFilter('parsed');
                setPage(1);
              }}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${
                parseStatusFilter === 'parsed'
                  ? 'bg-white text-indigo-700 shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Parsed Entries
            </button>
            <button
              onClick={() => {
                setParseStatusFilter('malformed');
                setPage(1);
              }}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${
                parseStatusFilter === 'malformed'
                  ? 'bg-white text-rose-700 shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Malformed / Unparsed
            </button>
          </div>

          {/* Severity Filter */}
          <div className="flex items-center space-x-1.5">
            <span className="text-slate-500 font-medium">Severity:</span>
            <select
              value={selectedLevel}
              onChange={(e) => {
                setSelectedLevel(e.target.value);
                setPage(1);
              }}
              className="bg-slate-50 border border-slate-200 rounded-md px-2 py-1 text-xs text-slate-700 font-medium focus:ring-1 focus:ring-indigo-500"
            >
              <option value="ALL">All Levels</option>
              <option value="ERROR">ERROR</option>
              <option value="WARNING">WARNING</option>
              <option value="INFO">INFO</option>
              <option value="DEBUG">DEBUG</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>

          {/* Service Filter */}
          {availableServices.length > 0 && (
            <div className="flex items-center space-x-1.5">
              <span className="text-slate-500 font-medium">Service:</span>
              <select
                value={selectedService}
                onChange={(e) => {
                  setSelectedService(e.target.value);
                  setPage(1);
                }}
                className="bg-slate-50 border border-slate-200 rounded-md px-2 py-1 text-xs text-slate-700 font-medium focus:ring-1 focus:ring-indigo-500 max-w-[140px]"
              >
                <option value="ALL">All Services</option>
                {availableServices.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Sort Control */}
          <div className="flex items-center space-x-1.5 ml-auto">
            <span className="text-slate-500 font-medium">Sort By:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-md px-2 py-1 text-xs text-slate-700 font-medium"
            >
              <option value="line_number">Line Number</option>
              <option value="timestamp">Timestamp</option>
              <option value="response_time_ms">Latency</option>
              <option value="level">Severity</option>
            </select>
            <button
              onClick={() => setSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))}
              className="px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded text-slate-600 font-mono text-xs uppercase"
            >
              {sortDir}
            </button>
          </div>
        </div>
      </div>

      {/* Log Records Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold select-none">
                <th className="py-2.5 px-3 w-16 text-center">Line</th>
                <th className="py-2.5 px-3 w-40">Timestamp</th>
                <th className="py-2.5 px-3 w-28">Severity</th>
                <th className="py-2.5 px-3 w-36">Service</th>
                <th className="py-2.5 px-3">Message</th>
                <th className="py-2.5 px-3 w-24 text-right">HTTP / RT</th>
                <th className="py-2.5 px-3 w-12 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-[12px]">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="text-center py-10 text-slate-400 font-sans">
                    Loading entries...
                  </td>
                </tr>
              ) : entries.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-10 text-slate-400 font-sans">
                    No matching log entries found for current filters.
                  </td>
                </tr>
              ) : (
                entries.map((e) => (
                  <tr
                    key={e.id}
                    className={`hover:bg-indigo-50/20 transition-colors ${
                      e.parse_status === 'malformed' ? 'bg-rose-50/30' : ''
                    }`}
                  >
                    <td className="py-2 px-3 text-center text-slate-400 text-[11px]">
                      {e.line_number}
                    </td>
                    <td className="py-2 px-3 text-slate-600 font-mono text-[11px] whitespace-nowrap">
                      {e.timestamp ? e.timestamp.replace('T', ' ').slice(0, 19) : '-'}
                    </td>
                    <td className="py-2 px-3 whitespace-nowrap font-sans">
                      {getLevelBadge(e.level)}
                    </td>
                    <td className="py-2 px-3 text-slate-700 font-sans font-medium truncate max-w-[140px]">
                      {e.service || '-'}
                    </td>
                    <td className="py-2 px-3 text-slate-900 break-words font-mono text-[11px] max-w-xl">
                      {e.message || e.raw_line}
                    </td>
                    <td className="py-2 px-3 text-right text-slate-600 text-[11px] whitespace-nowrap">
                      {e.status_code && (
                        <span
                          className={`px-1.5 py-0.5 rounded mr-1.5 font-bold ${
                            e.status_code >= 500
                              ? 'bg-rose-100 text-rose-800'
                              : e.status_code >= 400
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-emerald-100 text-emerald-800'
                          }`}
                        >
                          {e.status_code}
                        </span>
                      )}
                      {e.response_time_ms != null && (
                        <span className="text-slate-500 font-mono">
                          {e.response_time_ms.toFixed(0)}ms
                        </span>
                      )}
                    </td>
                    <td className="py-2 px-3 text-center">
                      <button
                        onClick={() => setInspectEntry(e)}
                        className="p-1 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded"
                        title="Inspect full raw entry"
                      >
                        <Maximize2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-3 bg-slate-50/80 border-t border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between text-xs text-slate-600 gap-2">
          <div>
            Showing <span className="font-semibold text-slate-800">{entries.length}</span> of{' '}
            <span className="font-semibold text-slate-800">{total}</span> records (Page {page} of{' '}
            {totalPages})
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
              className="bg-white border border-slate-200 rounded px-2 py-1 text-xs"
            >
              <option value={25}>25 / page</option>
              <option value={50}>50 / page</option>
              <option value={100}>100 / page</option>
              <option value={200}>200 / page</option>
            </select>

            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="p-1 rounded border border-slate-200 bg-white disabled:opacity-40 hover:bg-slate-100"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2 font-mono font-medium">{page}</span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="p-1 rounded border border-slate-200 bg-white disabled:opacity-40 hover:bg-slate-100"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Raw Entry Inspection Modal */}
      {inspectEntry && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-2xl w-full p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-bold text-slate-900">
                  Inspect Log Entry #{inspectEntry.line_number}
                </span>
                {getLevelBadge(inspectEntry.level)}
              </div>
              <button
                onClick={() => setInspectEntry(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Extracted Schema Fields */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs bg-slate-50 p-3.5 rounded-lg border border-slate-200">
              <div>
                <span className="text-slate-400 text-[10px] uppercase font-bold">Timestamp</span>
                <p className="font-mono text-slate-800">{inspectEntry.timestamp || 'N/A'}</p>
              </div>
              <div>
                <span className="text-slate-400 text-[10px] uppercase font-bold">Service</span>
                <p className="font-medium text-slate-800">{inspectEntry.service || 'N/A'}</p>
              </div>
              <div>
                <span className="text-slate-400 text-[10px] uppercase font-bold">Status Code</span>
                <p className="font-mono text-slate-800">{inspectEntry.status_code || 'N/A'}</p>
              </div>
              <div>
                <span className="text-slate-400 text-[10px] uppercase font-bold">Latency</span>
                <p className="font-mono text-slate-800">
                  {inspectEntry.response_time_ms != null
                    ? `${inspectEntry.response_time_ms} ms`
                    : 'N/A'}
                </p>
              </div>
              <div>
                <span className="text-slate-400 text-[10px] uppercase font-bold">Source IP</span>
                <p className="font-mono text-slate-800">{inspectEntry.source_ip || 'N/A'}</p>
              </div>
              <div>
                <span className="text-slate-400 text-[10px] uppercase font-bold">HTTP Method</span>
                <p className="font-mono text-slate-800">{inspectEntry.http_method || 'N/A'}</p>
              </div>
            </div>

            {/* Full Message */}
            <div>
              <span className="text-xs font-semibold text-slate-700">Parsed Message</span>
              <div className="mt-1 bg-slate-900 text-slate-100 p-3 rounded-lg font-mono text-xs whitespace-pre-wrap max-h-48 overflow-y-auto">
                {inspectEntry.message || 'No message field extracted'}
              </div>
            </div>

            {/* Original Raw Line */}
            <div>
              <span className="text-xs font-semibold text-slate-700">Original Raw Line (Preserved)</span>
              <div className="mt-1 bg-slate-100 text-slate-800 p-3 rounded-lg font-mono text-[11px] whitespace-pre-wrap max-h-40 overflow-y-auto border border-slate-200">
                {inspectEntry.raw_line}
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setInspectEntry(null)}
                className="px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-semibold hover:bg-slate-800"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

