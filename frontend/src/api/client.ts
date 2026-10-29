import {
  UploadResponse,
  DataQualityReport,
  DatasetProfile,
  LogAnalytics,
  ChartRecommendation,
  RecommendationEvaluation,
  EvaluationSummary,
  InvestigateResponse,
  PaginatedEntries,
  SampleItem,
} from '../types';

const API_BASE = '/api';

export const apiClient = {
  async checkHealth(): Promise<{ status: string; registered_parsers: string[] }> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  async getFormats(): Promise<{ formats: Array<{ id: string; name: string; description: string }> }> {
    const res = await fetch(`${API_BASE}/logs/formats`);
    if (!res.ok) throw new Error('Failed to fetch formats');
    return res.json();
  },

  async getSamples(): Promise<{ samples: SampleItem[] }> {
    const res = await fetch(`${API_BASE}/logs/samples`);
    if (!res.ok) throw new Error('Failed to fetch samples');
    return res.json();
  },

  async uploadLog(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/logs/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async loadSample(sampleName: string): Promise<UploadResponse> {
    const res = await fetch(`${API_BASE}/logs/sample/${sampleName}`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Sample loading failed' }));
      throw new Error(err.detail || 'Sample loading failed');
    }
    return res.json();
  },

  async parseLog(
    datasetId: string,
    formatName?: string,
    options?: Record<string, any>
  ): Promise<{
    status: string;
    dataset_id: string;
    format: string;
    data_quality: DataQualityReport;
    available_fields: string[];
  }> {
    const url = formatName
      ? `${API_BASE}/logs/${datasetId}/parse?format_name=${encodeURIComponent(formatName)}`
      : `${API_BASE}/logs/${datasetId}/parse`;

    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: options ? JSON.stringify(options) : undefined,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Parsing failed' }));
      throw new Error(err.detail || 'Parsing failed');
    }
    return res.json();
  },

  async getProfile(datasetId: string): Promise<DatasetProfile> {
    const res = await fetch(`${API_BASE}/logs/${datasetId}/profile`);
    if (!res.ok) throw new Error('Failed to get profile');
    return res.json();
  },

  async getEntries(
    datasetId: string,
    params: {
      search?: string;
      level?: string;
      service?: string;
      statusCode?: number;
      parseStatus?: string;
      page?: number;
      pageSize?: number;
      sortBy?: string;
      sortDir?: 'asc' | 'desc';
    }
  ): Promise<PaginatedEntries> {
    const query = new URLSearchParams();
    if (params.search) query.set('search', params.search);
    if (params.level && params.level !== 'ALL') query.set('level', params.level);
    if (params.service && params.service !== 'ALL') query.set('service', params.service);
    if (params.statusCode) query.set('status_code', params.statusCode.toString());
    if (params.parseStatus) query.set('parse_status', params.parseStatus);
    if (params.page) query.set('page', params.page.toString());
    if (params.pageSize) query.set('page_size', params.pageSize.toString());
    if (params.sortBy) query.set('sort_by', params.sortBy);
    if (params.sortDir) query.set('sort_dir', params.sortDir);

    const res = await fetch(`${API_BASE}/logs/${datasetId}/entries?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch entries');
    return res.json();
  },

  async getMalformed(datasetId: string): Promise<{
    dataset_id: string;
    total_malformed: number;
    malformed_entries: any[];
  }> {
    const res = await fetch(`${API_BASE}/logs/${datasetId}/malformed`);
    if (!res.ok) throw new Error('Failed to fetch malformed entries');
    return res.json();
  },

  async getAnalytics(datasetId: string): Promise<LogAnalytics> {
    const res = await fetch(`${API_BASE}/logs/${datasetId}/analytics`);
    if (!res.ok) throw new Error('Failed to get analytics');
    return res.json();
  },

  async getRecommendations(datasetId: string): Promise<ChartRecommendation[]> {
    const res = await fetch(`${API_BASE}/logs/${datasetId}/recommendations`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to get recommendations');
    return res.json();
  },

  async getVisualizations(
    datasetId: string,
    filters?: { service?: string; level?: string }
  ): Promise<any> {
    const query = new URLSearchParams();
    if (filters?.service && filters.service !== 'ALL') query.set('filter_service', filters.service);
    if (filters?.level && filters.level !== 'ALL') query.set('filter_level', filters.level);

    const res = await fetch(`${API_BASE}/logs/${datasetId}/visualizations?${query.toString()}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to fetch visualizations data');
    return res.json();
  },

  async investigate(datasetId: string, query: string): Promise<InvestigateResponse> {
    const res = await fetch(`${API_BASE}/logs/${datasetId}/investigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });
    if (!res.ok) throw new Error('Investigation failed');
    return res.json();
  },

  async recordEvaluation(
    datasetId: string,
    evaluation: RecommendationEvaluation
  ): Promise<EvaluationSummary> {
    const res = await fetch(`${API_BASE}/logs/${datasetId}/evaluations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(evaluation),
    });
    if (!res.ok) throw new Error('Failed to record evaluation');
    return res.json();
  },

  async getEvaluations(datasetId: string): Promise<EvaluationSummary> {
    const res = await fetch(`${API_BASE}/logs/${datasetId}/evaluations`);
    if (!res.ok) throw new Error('Failed to get evaluations');
    return res.json();
  },

  getExportUrl(datasetId: string, format: 'csv' | 'json' | 'unparsed' | 'html'): string {
    return `${API_BASE}/logs/${datasetId}/export?format=${format}`;
  },
};

