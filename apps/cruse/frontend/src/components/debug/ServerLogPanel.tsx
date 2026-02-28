'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { Box, MenuItem, Select, Typography } from '@mui/material';
import type { SelectChangeEvent } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useCruseStore } from '@/store/cruseStore';

const LEVEL_COLORS: Record<string, string> = {
  CRITICAL: '#ef4444',
  ERROR: '#ef4444',
  WARNING: '#eab308',
  INFO: '#06b6d4',
  DEBUG: '#6b7280',
};

const LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'];

function formatTime(ts: number): string {
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export function ServerLogPanel() {
  const entries = useCruseStore((s) => s.debugLogEntries);
  const darkMode = useCruseStore((s) => s.darkMode);
  const [minLevel, setMinLevel] = useState('DEBUG');
  const scrollRef = useRef<HTMLDivElement>(null);
  const isAutoScroll = useRef(true);

  const minLevelIndex = LEVELS.indexOf(minLevel);
  const filtered = entries.filter((e) => LEVELS.indexOf(e.level) >= minLevelIndex);

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

  const handleLevelChange = (event: SelectChangeEvent<string>) => {
    setMinLevel(event.target.value);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Filter bar */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 1.5, py: 1, borderBottom: '1px solid', borderColor: darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }}>
        <Typography variant="caption" sx={{ opacity: 0.6 }}>Min level:</Typography>
        <Select
          value={minLevel}
          onChange={handleLevelChange}
          size="small"
          sx={{ fontSize: '0.7rem', height: 28, minWidth: 90 }}
        >
          {LEVELS.map((l) => (
            <MenuItem key={l} value={l} sx={{ fontSize: '0.75rem' }}>
              {l}
            </MenuItem>
          ))}
        </Select>
        <Typography variant="caption" sx={{ ml: 'auto', opacity: 0.5 }}>
          {filtered.length} entries
        </Typography>
      </Box>

      {/* Log entries */}
      <Box
        ref={scrollRef}
        onScroll={handleScroll}
        sx={{
          flex: 1,
          overflow: 'auto',
          px: 1,
          py: 0.5,
          fontFamily: '"JetBrains Mono", "Fira Code", monospace',
          fontSize: '0.7rem',
          lineHeight: 1.6,
          '&::-webkit-scrollbar': { width: 6 },
          '&::-webkit-scrollbar-thumb': {
            bgcolor: darkMode ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.15)',
            borderRadius: 3,
          },
        }}
      >
        {filtered.length === 0 ? (
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', opacity: 0.4 }}>
            <Typography variant="body2" sx={{ fontFamily: 'inherit' }}>
              No log entries{entries.length > 0 ? ' at this level' : ' yet'}.
            </Typography>
          </Box>
        ) : (
          <AnimatePresence initial={false}>
            {filtered.map((entry) => {
              const color = LEVEL_COLORS[entry.level] || '#6b7280';
              return (
                <motion.div
                  key={entry.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.15 }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      gap: 1,
                      py: 0.25,
                      borderBottom: '1px solid',
                      borderColor: darkMode ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.03)',
                    }}
                  >
                    <Typography component="span" sx={{ color: '#6b7280', fontFamily: 'inherit', fontSize: 'inherit', flexShrink: 0 }}>
                      {formatTime(entry.timestamp)}
                    </Typography>
                    <Typography
                      component="span"
                      sx={{ color, fontWeight: 700, fontFamily: 'inherit', fontSize: 'inherit', flexShrink: 0, minWidth: 55 }}
                    >
                      {entry.level}
                    </Typography>
                    <Typography
                      component="span"
                      sx={{
                        fontFamily: 'inherit',
                        fontSize: 'inherit',
                        opacity: 0.85,
                        wordBreak: 'break-word',
                        whiteSpace: 'pre-wrap',
                      }}
                    >
                      {entry.message}
                    </Typography>
                  </Box>
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
      </Box>
    </Box>
  );
}
