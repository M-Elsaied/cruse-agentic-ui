import { create } from 'zustand';
import type { AgentTraceEntry, ServerLogEntry } from '@/types/debug';
import type { ConversationDetail, ConversationSummary } from '@/types/history';
import type { ConnectivityData } from '@/types/network';
import type { BackgroundTheme } from '@/types/theme';
import type { WidgetCardDefinition } from '@/types/widget';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

export interface AgentActivity {
  status: 'idle' | 'thinking' | 'responding';
  agents: string[];
}

interface CruseState {
  // Session
  sessionId: string | null;
  agentNetwork: string | null;
  availableSystems: string[];

  // Chat
  messages: ChatMessage[];
  isStreaming: boolean;
  streamingContent: string;
  sampleQueries: string[];

  // Widget
  widgetSchema: WidgetCardDefinition | null;
  widgetFormData: Record<string, unknown>;

  // Theme
  theme: BackgroundTheme | null;

  // Agent activity
  agentActivity: AgentActivity;

  // Connection
  isConnected: boolean;
  connectionError: string | null;

  // Debug monitor
  debugDrawerOpen: boolean;
  debugTraceEntries: AgentTraceEntry[];
  debugLogEntries: ServerLogEntry[];
  debugUnreadCount: number;
  debugActiveTab: number;

  // Network visualization
  networkDrawerOpen: boolean;
  connectivityData: ConnectivityData | null;
  connectivityLoading: boolean;

  // Auth
  userRole: 'admin' | 'user' | null;
  adminDrawerOpen: boolean;

  // Rate limiting
  rateLimitRemaining: number | null;
  rateLimitTotal: number | null;
  rateLimitExceeded: boolean;

  // History
  historyDrawerOpen: boolean;
  conversationHistory: ConversationSummary[];
  historyLoading: boolean;
  viewingConversation: ConversationDetail | null;

  // UI
  darkMode: boolean;
  pendingInput: string | null;
  widgetSubmitted: boolean;
  widgetDrawerOpen: boolean;

  // Tour
  tourActive: boolean;
  tourStep: number;

  // Actions
  setSessionId: (id: string | null) => void;
  setAgentNetwork: (network: string | null) => void;
  setAvailableSystems: (systems: string[]) => void;
  setSampleQueries: (queries: string[]) => void;
  addMessage: (message: ChatMessage) => void;
  clearMessages: () => void;
  setIsStreaming: (streaming: boolean) => void;
  setStreamingContent: (content: string) => void;
  appendStreamingContent: (delta: string) => void;
  setWidgetSchema: (schema: WidgetCardDefinition | null) => void;
  setWidgetFormData: (data: Record<string, unknown>) => void;
  setTheme: (theme: BackgroundTheme | null) => void;
  setAgentActivity: (activity: AgentActivity) => void;
  setIsConnected: (connected: boolean) => void;
  setConnectionError: (error: string | null) => void;
  toggleDarkMode: () => void;
  setPendingInput: (input: string | null) => void;
  setWidgetSubmitted: (submitted: boolean) => void;
  toggleDebugDrawer: () => void;
  addTraceEntry: (entry: AgentTraceEntry) => void;
  addLogEntry: (entry: ServerLogEntry) => void;
  clearDebugEntries: () => void;
  setDebugActiveTab: (tab: number) => void;
  setUserRole: (role: 'admin' | 'user' | null) => void;
  toggleAdminDrawer: () => void;
  toggleNetworkDrawer: () => void;
  setConnectivityData: (data: ConnectivityData | null) => void;
  setConnectivityLoading: (loading: boolean) => void;
  toggleWidgetDrawer: () => void;
  setWidgetDrawerOpen: (open: boolean) => void;
  setRateLimit: (remaining: number | null, limit: number | null) => void;
  setRateLimitExceeded: (exceeded: boolean) => void;
  toggleHistoryDrawer: () => void;
  setConversationHistory: (conversations: ConversationSummary[]) => void;
  setHistoryLoading: (loading: boolean) => void;
  setViewingConversation: (detail: ConversationDetail | null) => void;
  setTourStep: (step: number) => void;
  endTour: () => void;
  reset: () => void;
}

const initialState = {
  sessionId: null,
  agentNetwork: null,
  availableSystems: [],
  messages: [],
  sampleQueries: [],
  isStreaming: false,
  streamingContent: '',
  widgetSchema: null,
  widgetFormData: {},
  theme: null,
  agentActivity: { status: 'idle' as const, agents: [] },
  isConnected: false,
  connectionError: null,
  debugDrawerOpen: false,
  debugTraceEntries: [],
  debugLogEntries: [],
  debugUnreadCount: 0,
  debugActiveTab: 0,
  userRole: null,
  adminDrawerOpen: false,
  networkDrawerOpen: false,
  connectivityData: null,
  connectivityLoading: false,
  rateLimitRemaining: null,
  rateLimitTotal: null,
  rateLimitExceeded: false,
  historyDrawerOpen: false,
  conversationHistory: [],
  historyLoading: false,
  viewingConversation: null,
  darkMode: true,
  pendingInput: null,
  widgetSubmitted: false,
  widgetDrawerOpen: false,
  tourActive: true,
  tourStep: 0,
};

export const useCruseStore = create<CruseState>((set) => ({
  ...initialState,

  setSessionId: (id) => set({ sessionId: id }),
  setAgentNetwork: (network) => set({ agentNetwork: network }),
  setAvailableSystems: (systems) => set({ availableSystems: systems }),
  setSampleQueries: (queries) => set({ sampleQueries: queries }),

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  clearMessages: () => set({ messages: [] }),

  setIsStreaming: (streaming) => set({ isStreaming: streaming }),
  setStreamingContent: (content) => set({ streamingContent: content }),
  appendStreamingContent: (delta) =>
    set((state) => ({ streamingContent: state.streamingContent + delta })),

  setWidgetSchema: (schema) => set({ widgetSchema: schema, widgetFormData: {} }),
  setWidgetFormData: (data) => set({ widgetFormData: data }),
  setTheme: (theme) => set({ theme: theme }),
  setAgentActivity: (activity) => set({ agentActivity: activity }),

  setIsConnected: (connected) => set({ isConnected: connected }),
  setConnectionError: (error) => set({ connectionError: error }),

  toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),
  setPendingInput: (input) => set({ pendingInput: input }),
  setWidgetSubmitted: (submitted) => set({ widgetSubmitted: submitted }),

  toggleDebugDrawer: () =>
    set((state) => ({
      debugDrawerOpen: !state.debugDrawerOpen,
      debugUnreadCount: !state.debugDrawerOpen ? 0 : state.debugUnreadCount,
    })),
  addTraceEntry: (entry) =>
    set((state) => ({
      debugTraceEntries: [...state.debugTraceEntries, entry],
      debugUnreadCount: state.debugDrawerOpen ? state.debugUnreadCount : state.debugUnreadCount + 1,
    })),
  addLogEntry: (entry) =>
    set((state) => ({
      debugLogEntries: [...state.debugLogEntries, entry],
      debugUnreadCount: state.debugDrawerOpen ? state.debugUnreadCount : state.debugUnreadCount + 1,
    })),
  clearDebugEntries: () => set({ debugTraceEntries: [], debugLogEntries: [], debugUnreadCount: 0 }),
  setDebugActiveTab: (tab) => set({ debugActiveTab: tab }),

  setUserRole: (role) => set({ userRole: role }),
  toggleAdminDrawer: () =>
    set((state) => ({ adminDrawerOpen: !state.adminDrawerOpen })),

  toggleNetworkDrawer: () =>
    set((state) => ({ networkDrawerOpen: !state.networkDrawerOpen })),
  setConnectivityData: (data) => set({ connectivityData: data }),
  setConnectivityLoading: (loading) => set({ connectivityLoading: loading }),

  toggleWidgetDrawer: () =>
    set((state) => ({ widgetDrawerOpen: !state.widgetDrawerOpen })),
  setWidgetDrawerOpen: (open) => set({ widgetDrawerOpen: open }),

  setRateLimit: (remaining, limit) => set({ rateLimitRemaining: remaining, rateLimitTotal: limit }),
  setRateLimitExceeded: (exceeded) => set({ rateLimitExceeded: exceeded }),

  toggleHistoryDrawer: () =>
    set((state) => ({ historyDrawerOpen: !state.historyDrawerOpen })),
  setConversationHistory: (conversations) => set({ conversationHistory: conversations }),
  setHistoryLoading: (loading) => set({ historyLoading: loading }),
  setViewingConversation: (detail) => set({ viewingConversation: detail }),

  setTourStep: (step) => set({ tourStep: step }),
  endTour: () => set({ tourActive: false, tourStep: 0 }),

  reset: () =>
    set({
      ...initialState,
      // Preserve these across resets
      availableSystems: useCruseStore.getState().availableSystems,
      darkMode: useCruseStore.getState().darkMode,
      userRole: useCruseStore.getState().userRole,
      adminDrawerOpen: useCruseStore.getState().adminDrawerOpen,
      networkDrawerOpen: useCruseStore.getState().networkDrawerOpen,
      rateLimitRemaining: useCruseStore.getState().rateLimitRemaining,
      rateLimitTotal: useCruseStore.getState().rateLimitTotal,
      rateLimitExceeded: useCruseStore.getState().rateLimitExceeded,
    }),
}));
