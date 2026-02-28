'use client';

import { useEffect, useRef, useCallback } from 'react';
import { Box, Chip, Typography } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useCruseStore } from '@/store/cruseStore';

const TYPE_COLORS: Record<string, string> = {
  AGENT: '#3b82f6',
  AI: '#a855f7',
  AGENT_TOOL_RESULT: '#22c55e',
  AGENT_FRAMEWORK: '#f97316',
  AGENT_PROGRESS: '#06b6d4',
  HUMAN: '#ec4899',
  SYSTEM: '#94a3b8',
  UNKNOWN: '#64748b',
};

function formatTime(ts: number): string {
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export function AgentTracePanel() {
  const entries = useCruseStore((s) => s.debugTraceEntries);
  const darkMode = useCruseStore((s) => s.darkMode);
  const scrollRef = useRef<HTMLDivElement>(null);
  const isAutoScroll = useRef(true);

  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    isAutoScroll.current = atBottom;
  }, []);

  useEffect(() => {
    if (isAutoScroll.current && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [entries.length]);

  if (entries.length === 0) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', opacity: 0.4 }}>
        <Typography variant="body2">No agent trace events yet. Send a message to see activity.</Typography>
      </Box>
    );
  }

  return (
    <Box
      ref={scrollRef}
      onScroll={handleScroll}
      sx={{
        flex: 1,
        overflow: 'auto',
        px: 1.5,
        py: 1,
        '&::-webkit-scrollbar': { width: 6 },
        '&::-webkit-scrollbar-thumb': {
          bgcolor: darkMode ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.15)',
          borderRadius: 3,
        },
      }}
    >
      <AnimatePresence initial={false}>
        {entries.map((entry) => {
          const color = TYPE_COLORS[entry.type] || TYPE_COLORS.UNKNOWN;
          return (
            <motion.div
              key={entry.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2 }}
              style={{ marginBottom: 8 }}
            >
              <Box
                sx={{
                  p: 1.5,
                  borderRadius: 1.5,
                  bgcolor: darkMode ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)',
                  borderLeft: `3px solid ${color}`,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                  <Chip
                    label={entry.type}
                    size="small"
                    sx={{
                      bgcolor: `${color}22`,
                      color,
                      fontWeight: 600,
                      fontSize: '0.65rem',
                      height: 20,
                    }}
                  />
                  {entry.agent && (
                    <Typography
                      variant="caption"
                      sx={{ fontWeight: 700, color: darkMode ? '#e2e8f0' : '#1e293b' }}
                    >
                      {entry.agent}
                    </Typography>
                  )}
                  <Typography variant="caption" sx={{ ml: 'auto', opacity: 0.5, fontSize: '0.65rem' }}>
                    {formatTime(entry.timestamp)}
                  </Typography>
                </Box>
                {entry.text && (
                  <Typography
                    variant="body2"
                    sx={{
                      fontSize: '0.75rem',
                      opacity: 0.85,
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      maxHeight: 120,
                      overflow: 'hidden',
                      lineHeight: 1.5,
                    }}
                  >
                    {entry.text.length > 500 ? entry.text.slice(0, 500) + '...' : entry.text}
                  </Typography>
                )}
                {entry.has_structure && (
                  <Chip label="has structure" size="small" variant="outlined" sx={{ mt: 0.5, height: 18, fontSize: '0.6rem' }} />
                )}
              </Box>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </Box>
  );
}
