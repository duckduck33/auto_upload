// API 관련 타입들
export interface AutomationRequest {
  keyword: string;
  postCount: number; // 항상 1
}

export interface AutomationResponse {
  success: boolean;
  message: string;
  taskId?: string;
}

export interface LogEntry {
  timestamp: string;
  message: string;
  level: 'info' | 'warning' | 'error';
}

export interface GeneratedPost {
  id: string;
  title: string;
  content: string;
  createdAt: string;
}

export interface AutomationStatus {
  isRunning: boolean;
  progress: number;
  status: string;
  currentStep: number;
  totalSteps: number;
  stepDescription: string;
}

// UI 상태 타입들
export interface AppState {
  keyword: string;
  postCount: number; // 항상 1
  isRunning: boolean;
  status: string;
  progress: number;
  logs: string[];
  generatedPosts: GeneratedPost[];
  activeTab: 'logs' | 'generating' | 'posts';
}

// 컴포넌트 Props 타입들
export interface KeywordInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  error?: string;
}

export interface AutomationControlsProps {
  isRunning: boolean;
  onStart: () => void;
  onStop: () => void;
  disabled?: boolean;
  loading?: boolean;
}

export interface StatusDisplayProps {
  status: string;
  progress: number;
  className?: string;
}

export interface LogViewerProps {
  logs: string[];
  onClearLogs: () => void;
  className?: string;
}

export interface GeneratedPostViewerProps {
  posts: GeneratedPost[];
  className?: string;
}

export interface ProgressMonitorProps {
  currentStep: number;
  totalSteps: number;
  stepDescription: string;
  className?: string;
}

// 이벤트 핸들러 타입들
export type AutomationEventHandler = () => void;
export type KeywordChangeHandler = (keyword: string) => void;
export type TabChangeHandler = (tabId: string) => void; 