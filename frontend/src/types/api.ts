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
  // Agentic RAG fields
  agent_plan?: string | null;
  tool_calls?: Array<{
    tool_name: string;
    arguments: Record<string, unknown>;
    iteration: number;
  }>;
  iterations?: number;
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
  user_id: string;
  started_at: string;
  completed_at?: string;
  current_step: string;
  steps: ProcessingStep[];
  answer?: string;
  sources_count?: number;
  error?: string;
  // Agentic RAG fields
  agent_plan?: string | null;
  tool_calls?: Array<{
    tool_name: string;
    arguments: Record<string, unknown>;
    iteration: number;
  }>;
  iterations?: number;
  retrieved_documents?: Array<{
    filename: string;
    title: string;
    score: number;
    chunk_id: string;
    text_preview: string;
  }>;
  duration_seconds?: number;
}
