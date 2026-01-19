
export enum AgentRole {
  COMMANDER = '$meat',
  AUDITOR = '$AIMEAT',
  ARCHIVAR = '$thespy'
}

export type GeminiModel = 
  | 'gemini-2.0-flash-exp' 
  | 'gemini-1.5-flash' 
  | 'gemini-1.5-pro' 
  | 'gemini-flash-lite-latest';

export interface BicameralConfig {
  model: GeminiModel;
  temperature: number;
  topP: number;
  topK: number;
  apiTier: 'FREE' | 'STUDIO_PAID' | 'VERTEX';
  voiceEnabled: boolean;
  zoomLevel: number;
  highVisibility: boolean;
}

export interface SystemFile {
  id: string;
  name: string;
  size: string;
  type: string;
  content?: string;
  dataUrl?: string;
  timestamp: string;
}

export interface ChatAttachment {
  mimeType: string;
  data: string; // base64
  name: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  agent: AgentRole;
  content: string;
  timestamp: Date;
  attachments?: ChatAttachment[];
  audioBase64?: string;
}

export interface RFC {
  id: string;
  title: string;
  category: string;
  status: 'RATIFIED' | 'PROPOSAL' | 'DRAFT';
  content: string;
}

export interface AuditResult {
  passed: boolean;
  score: number;
  findings: string[];
  protocolV5Compliance: boolean;
}

export interface BlackOpsTestResult {
  integrity: number;
  stealth: number;
  sovereignty: boolean;
  leaks: string[];
  verdict: 'GO' | 'NO-GO';
}

export interface LogEntry {
  id: string;
  timestamp: string;
  message: string;
  type: 'info' | 'error' | 'success' | 'warning' | 'incident' | 'blackops' | 'deploy';
}

export interface SystemStatus {
  project: string;
  clearance: string;
  mode: string;
  target: string;
  sshStatus: string;
}
