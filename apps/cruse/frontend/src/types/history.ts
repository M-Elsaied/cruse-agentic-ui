export interface ConversationSummary {
  id: number;
  session_id: string;
  agent_network: string;
  title: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface HistoryMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ConversationDetail {
  conversation: ConversationSummary;
  messages: HistoryMessage[];
}