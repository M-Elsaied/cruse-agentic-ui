import { useCallback, useEffect, useRef } from 'react';
import { useAuth } from '@clerk/nextjs';
import { useCruseStore } from '@/store/cruseStore';
import type { WidgetCardDefinition } from '@/types/widget';

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:5001';
const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECT_ATTEMPTS = 5;

// generateId() is unavailable on plain HTTP; fall back to Math.random
function generateId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
}

interface ServerEvent {
  type: string;
  data: unknown;
}

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const { getToken } = useAuth();

  const sessionId = useCruseStore((s) => s.sessionId);
  const setIsConnected = useCruseStore((s) => s.setIsConnected);
  const setConnectionError = useCruseStore((s) => s.setConnectionError);
  const addMessage = useCruseStore((s) => s.addMessage);
  const setIsStreaming = useCruseStore((s) => s.setIsStreaming);
  const setStreamingContent = useCruseStore((s) => s.setStreamingContent);
  const appendStreamingContent = useCruseStore((s) => s.appendStreamingContent);
  const setWidgetSchema = useCruseStore((s) => s.setWidgetSchema);
  const setTheme = useCruseStore((s) => s.setTheme);
  const setAgentActivity = useCruseStore((s) => s.setAgentActivity);
  const addTraceEntry = useCruseStore((s) => s.addTraceEntry);
  const addLogEntry = useCruseStore((s) => s.addLogEntry);
  const setRateLimit = useCruseStore((s) => s.setRateLimit);
  const setRateLimitExceeded = useCruseStore((s) => s.setRateLimitExceeded);

  const handleEvent = useCallback(
    (event: ServerEvent) => {
      switch (event.type) {
        case 'chat_token':
          appendStreamingContent(event.data as string);
          break;

        case 'chat_complete':
          addMessage({
            id: generateId(),
            role: 'assistant',
            content: event.data as string,
            timestamp: Date.now(),
          });
          break;

        case 'widget_schema': {
          const raw = event.data as Record<string, unknown>;
          // Check for display:false (agent says no widget needed)
          if (raw && raw.display === false) {
            setWidgetSchema(null);
          } else {
            setWidgetSchema(raw as unknown as WidgetCardDefinition);
          }
          break;
        }

        case 'theme':
          setTheme(event.data as any);
          break;

        case 'agent_activity':
          setAgentActivity(event.data as any);
          break;

        case 'agent_trace':
          addTraceEntry({ ...(event.data as any), id: generateId() });
          break;

        case 'server_log':
          addLogEntry({ ...(event.data as any), id: generateId() });
          break;

        case 'rate_limit': {
          const rl = event.data as { allowed: boolean; remaining: number; limit: number };
          setRateLimit(Math.max(0, rl.remaining), rl.limit);
          if (!rl.allowed) {
            setRateLimitExceeded(true);
            setIsStreaming(false);
            setStreamingContent('');
            addMessage({
              id: generateId(),
              role: 'assistant',
              content: 'You have reached your daily request limit. Please try again tomorrow.',
              timestamp: Date.now(),
            });
          }
          break;
        }

        case 'done':
          setIsStreaming(false);
          setStreamingContent('');
          setAgentActivity({ status: 'idle', agents: [] });
          break;

        case 'error':
          setIsStreaming(false);
          setStreamingContent('');
          const errData = event.data as { message?: string } | null;
          setConnectionError(errData?.message || 'Unknown error');
          break;
      }
    },
    [
      addMessage,
      addLogEntry,
      addTraceEntry,
      appendStreamingContent,
      setAgentActivity,
      setConnectionError,
      setIsStreaming,
      setRateLimit,
      setRateLimitExceeded,
      setStreamingContent,
      setTheme,
      setWidgetSchema,
    ]
  );

  const connect = useCallback(async () => {
    if (!sessionId) return;

    const token = await getToken();
    if (!token) return;

    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    const ws = new WebSocket(`${WS_BASE_URL}/ws/chat/${sessionId}?token=${encodeURIComponent(token)}`);

    ws.onopen = () => {
      setIsConnected(true);
      setConnectionError(null);
      reconnectAttempts.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const parsed: ServerEvent = JSON.parse(event.data);
        handleEvent(parsed);
      } catch {
        console.error('Failed to parse WebSocket message:', event.data);
      }
    };

    ws.onclose = (event) => {
      setIsConnected(false);
      wsRef.current = null;

      // Don't reconnect if closed intentionally (4xxx codes or clean close)
      if (event.code >= 4000 || event.code === 1000) return;

      // Auto-reconnect
      if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts.current++;
        reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY_MS);
      } else {
        setConnectionError('Connection lost. Please refresh the page.');
      }
    };

    ws.onerror = () => {
      setConnectionError('WebSocket connection error');
    };

    wsRef.current = ws;
  }, [sessionId, getToken, handleEvent, setIsConnected, setConnectionError]);

  // Connect when sessionId changes
  useEffect(() => {
    connect();

    return () => {
      clearTimeout(reconnectTimer.current);
      if (wsRef.current) {
        wsRef.current.close(1000);
        wsRef.current = null;
      }
    };
  }, [connect]);

  const sendMessage = useCallback(
    (text: string, formData?: Record<string, unknown>) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        setConnectionError('Not connected. Please wait or refresh.');
        return;
      }

      // Add user message to store
      addMessage({
        id: generateId(),
        role: 'user',
        content: text,
        timestamp: Date.now(),
      });

      setIsStreaming(true);
      setConnectionError(null);

      wsRef.current.send(
        JSON.stringify({
          text,
          form_data: formData || null,
        })
      );
    },
    [addMessage, setIsStreaming, setConnectionError]
  );

  return { sendMessage, isConnected: !!wsRef.current };
}
