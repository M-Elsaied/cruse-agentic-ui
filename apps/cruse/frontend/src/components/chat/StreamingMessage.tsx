'use client';

import { Box, Avatar } from '@mui/material';
import { SmartToy } from '@mui/icons-material';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface StreamingMessageProps {
  content: string;
  darkMode: boolean;
}

/**
 * Displays streaming content with a blinking cursor at the end.
 */
export function StreamingMessage({ content, darkMode }: StreamingMessageProps) {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start' }}>
        <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main', fontSize: 16 }}>
          <SmartToy fontSize="small" />
        </Avatar>
        <Box
          sx={{
            maxWidth: '80%',
            px: 2,
            py: 1.5,
            borderRadius: 2,
            bgcolor: darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)',
          }}
        >
          <Box className="markdown-content" sx={{ '& > *:last-child': { mb: 0 } }}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {content}
            </ReactMarkdown>
            {/* Blinking cursor */}
            <Box
              component="span"
              sx={{
                display: 'inline-block',
                width: 2,
                height: '1em',
                bgcolor: 'primary.main',
                ml: 0.5,
                animation: 'pulse 1s ease-in-out infinite',
                verticalAlign: 'text-bottom',
              }}
            />
          </Box>
        </Box>
      </Box>
    </motion.div>
  );
}
