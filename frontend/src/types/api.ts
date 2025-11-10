export interface QueryRequest {
  query: string;
  company_id?: number | null;
  session_id?: string | null;
  user_id?: string;
  top_k?: number;
}

export interface QueryResponse {
  answer: string;
  sources: Record<string, unknown>[];
  conversation_id: number;
  session_id: string;
  metadata?: Record<string, unknown> | null;
}

export interface ProcessingStep {
  step: string;
  status: string;
  timestamp: string;
  details?: string;
}

export interface QueryStatus {
  query_id: string;
  status: 'started' | 'in_progress' | 'completed' | 'error';
  query: string;
  started_at: string;
  completed_at?: string;
  current_step: string;
  steps: ProcessingStep[];
  answer?: string;
  sources_count?: number;
  error?: string;
}
