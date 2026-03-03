'use client';

import { useState } from 'react';
import { Box, Avatar, IconButton, Tooltip, Typography } from '@mui/material';
import { SmartToy, Person, ContentCopy, Check } from '@mui/icons-material';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ChatMessage } from '@/store/cruseStore';

interface MessageBubbleProps {
  message: ChatMessage;
  darkMode: boolean;
  index: number;
}

export function MessageBubble({ message, darkMode, index }: MessageBubbleProps) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: Math.min(index * 0.05, 0.3) }}
    >
      <Box
        sx={{
          display: 'flex',
          gap: 1.5,
          alignItems: 'flex-start',
          flexDirection: isUser ? 'row-reverse' : 'row',
          '&:hover .copy-btn': { opacity: 1 },
        }}
      >
        <Avatar
          sx={{
            width: 32,
            height: 32,
            bgcolor: isUser ? 'primary.main' : 'secondary.main',
            fontSize: 16,
          }}
        >
          {isUser ? <Person fontSize="small" /> : <SmartToy fontSize="small" />}
        </Avatar>

        <Box sx={{ position: 'relative', maxWidth: { xs: '85%', md: '80%' }, minWidth: 0 }}>
          <Box
            sx={{
              px: 2,
              py: 1.5,
              borderRadius: 2,
              bgcolor: isUser
                ? 'primary.main'
                : darkMode
                  ? 'rgba(255,255,255,0.06)'
                  : 'rgba(0,0,0,0.04)',
              color: isUser ? 'white' : 'text.primary',
              transition: 'transform 0.15s',
              '&:hover': { transform: 'translateY(-1px)' },
            }}
          >
            {isUser ? (
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'break-word', wordBreak: 'break-word' }}>
                {message.content}
              </Typography>
            ) : (
              <Box className="markdown-content" sx={{ '& > *:last-child': { mb: 0 }, overflowWrap: 'break-word', wordBreak: 'break-word', overflow: 'hidden' }}>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </Box>
            )}
          </Box>

          {/* Copy button (visible on hover) */}
          {!isUser && (
            <Tooltip title={copied ? 'Copied!' : 'Copy'}>
              <IconButton
                className="copy-btn"
                size="small"
                onClick={handleCopy}
                sx={{
                  position: 'absolute',
                  top: 4,
                  right: -36,
                  opacity: 0,
                  transition: 'opacity 0.2s',
                }}
              >
                {copied ? (
                  <Check fontSize="small" color="success" />
                ) : (
                  <ContentCopy fontSize="small" sx={{ fontSize: 14 }} />
                )}
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Box>
    </motion.div>
  );
}
