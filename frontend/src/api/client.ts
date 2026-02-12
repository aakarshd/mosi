const API_BASE = '/api/v1';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem('mosi_token') || '';
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Screener
  getScreenerStocks: (model: string, page = 1) =>
    request(`/screener/${model}?page=${page}`),

  getScreenerDetail: (model: string, stockId: number) =>
    request(`/screener/${model}/${stockId}`),

  // Analysis
  getAnalysis: (stockId: number) =>
    request(`/analysis/${stockId}`),

  getAnalysisSummary: (stockId: number) =>
    request(`/analysis/${stockId}/summary`),

  // Readiness
  getReadinessList: (status?: string, page = 1) =>
    request(`/readiness?page=${page}${status ? `&status=${status}` : ''}`),

  getReadinessDetail: (stockId: number) =>
    request(`/readiness/${stockId}`),

  getTransitions: (stockId: number) =>
    request(`/readiness/transitions/${stockId}`),

  // Portfolio
  getPortfolio: () => request('/portfolio'),
  getPortfolioMetrics: () => request('/portfolio/metrics'),
  getCompliance: (stockId: number) => request(`/portfolio/${stockId}/compliance`),

  // Journal
  getJournalEntries: (page = 1) => request(`/journal?page=${page}`),
  createJournalEntry: (data: Record<string, unknown>) =>
    request('/journal', { method: 'POST', body: JSON.stringify(data) }),
  getBehavioralReport: () => request('/journal/behavioral'),
  getBehavioralHistory: () => request('/journal/behavioral/history'),

  // Config
  getModelSelections: () => request('/config/models'),
  updateModelSelections: (data: Record<string, unknown>) =>
    request('/config/models', { method: 'PUT', body: JSON.stringify(data) }),
  getTradingRules: () => request('/config/trading-rules'),
  updateTradingRules: (data: Record<string, unknown>) =>
    request('/config/trading-rules', { method: 'PUT', body: JSON.stringify(data) }),
  getAlertPreferences: () => request('/config/alerts'),
  updateAlertPreferences: (data: Record<string, unknown>) =>
    request('/config/alerts', { method: 'PUT', body: JSON.stringify(data) }),
};
