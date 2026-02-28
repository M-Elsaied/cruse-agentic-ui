'use client';

import { Box, Avatar, Typography } from '@mui/material';
import { SmartToy } from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useCruseStore } from '@/store/cruseStore';

export function TypingIndicator() {
  const agentActivity = useCruseStore((s) => s.agentActivity);
  const agentName =
    agentActivity?.agents?.length > 0
      ? agentActivity.agents[agentActivity.agents.length - 1]
      : null;

  return (
    <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start' }}>
      <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main', fontSize: 16 }}>
        <SmartToy fontSize="small" />
      </Avatar>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          px: 2,
          py: 1.5,
          borderRadius: 2,
          bgcolor: 'rgba(255,255,255,0.06)',
        }}
      >
        {agentName && (
          <Typography
            variant="caption"
            sx={{ color: 'primary.main', fontWeight: 600, mr: 0.5 }}
          >
            {agentName}
          </Typography>
        )}
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            animate={{ y: [0, -6, 0] }}
            transition={{
              duration: 0.6,
              repeat: Infinity,
              delay: i * 0.15,
              ease: 'easeInOut',
            }}
          >
            <Box
              sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                bgcolor: 'primary.main',
                opacity: 0.7,
              }}
            />
          </motion.div>
        ))}
      </Box>
    </Box>
  );
}
