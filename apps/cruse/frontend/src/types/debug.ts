export interface AgentTraceEntry {
  id: string;
  timestamp: number;
  agent: string;
  origin: string;
  type: string;
  text: string;
  has_structure: boolean;
}

export interface ServerLogEntry {
  id: string;
  timestamp: number;
  level: string;
  logger: string;
  message: string;
}
