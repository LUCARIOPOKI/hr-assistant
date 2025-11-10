import { QueryRequest, QueryResponse, QueryStatus } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const api = {
  async query(request: QueryRequest): Promise<QueryResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || 'Failed to submit query');
    }

    return response.json();
  },

  async getStatus(queryId: string): Promise<QueryStatus> {
    const response = await fetch(`${API_BASE_URL}/api/v1/status/${queryId}`);

    if (!response.ok) {
      throw new Error('Failed to get query status');
    }

    return response.json();
  },

  async clearStatus(queryId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/v1/status/${queryId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to clear query status');
    }
  },

  async health(): Promise<{
    status: string;
    version: string;
    timestamp: string;
    checks?: Record<string, unknown>;
    errors?: string[];
  }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/health`);

    if (!response.ok) {
      throw new Error('Failed to check health');
    }

    return response.json();
  },
};
