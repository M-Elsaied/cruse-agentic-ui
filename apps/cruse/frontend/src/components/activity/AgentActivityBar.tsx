'use client';

import { Box, Chip, Typography } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useCruseStore } from '@/store/cruseStore';

/**
 * Horizontal bar below the header showing the active agent chain.
 * Renders connected agent nodes with animated arrows, highlighting the
 * currently active (last) agent.
 */
export function AgentActivityBar() {
  const agentActivity = useCruseStore((s) => s.agentActivity);
  const isStreaming = useCruseStore((s) => s.isStreaming);

  if (!isStreaming || agentActivity.status === 'idle' || agentActivity.agents.length === 0) {
    return null;
  }

  const agents = agentActivity.agents;
  const activeAgent = agents[agents.length - 1];

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 0.75,
        px: { xs: 1, md: 2 },
        py: 0.75,
        zIndex: 2,
        position: 'relative',
        overflowX: 'auto',
        overflowY: 'hidden',
        '&::-webkit-scrollbar': { display: 'none' },
        scrollbarWidth: 'none',
      }}
    >
      <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 500, mr: 0.5, flexShrink: 0 }}>
        Agent chain:
      </Typography>
      <AnimatePresence>
        {agents.map((agent, i) => {
          const isActive = agent === activeAgent;
          return (
            <motion.div
              key={agent}
              initial={{ opacity: 0, scale: 0.8, x: -10 }}
              animate={{ opacity: 1, scale: 1, x: 0 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ delay: i * 0.1 }}
              style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}
            >
              {/* Arrow connector before this agent (except the first) */}
              {i > 0 && (
                <motion.div
                  initial={{ opacity: 0, scaleX: 0 }}
                  animate={{ opacity: 1, scaleX: 1 }}
                  transition={{ delay: i * 0.1 - 0.05 }}
                  style={{ display: 'flex', alignItems: 'center' }}
                >
                  <Box
                    sx={{
                      width: 16,
                      height: 2,
                      bgcolor: 'primary.main',
                      opacity: 0.4,
                      borderRadius: 1,
                    }}
                  />
                  <Box
                    sx={{
                      width: 0,
                      height: 0,
                      borderLeft: '5px solid',
                      borderTop: '4px solid transparent',
                      borderBottom: '4px solid transparent',
                      borderLeftColor: 'primary.main',
                      opacity: 0.4,
                    }}
                  />
                </motion.div>
              )}

              <Chip
                label={agent}
                size="small"
                variant={isActive ? 'filled' : 'outlined'}
                color="primary"
                sx={{
                  fontSize: '0.7rem',
                  height: 24,
                  fontWeight: isActive ? 700 : 400,
                  ...(isActive && {
                    animation: 'pulse 1.5s ease-in-out infinite',
                    boxShadow: '0 0 10px rgba(59,130,246,0.4)',
                  }),
                }}
              />
            </motion.div>
          );
        })}
      </AnimatePresence>

      {/* Status label for the active agent */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: agents.length * 0.1 }}
      >
        <Typography
          variant="caption"
          sx={{
            color: 'text.secondary',
            fontStyle: 'italic',
            ml: 0.5,
            opacity: 0.7,
          }}
        >
          {agentActivity.status === 'thinking' ? 'thinking...' : 'responding...'}
        </Typography>
      </motion.div>
    </Box>
  );
}
