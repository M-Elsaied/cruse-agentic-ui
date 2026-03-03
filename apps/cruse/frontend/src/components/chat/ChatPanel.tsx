'use client';

import { useEffect, useRef } from 'react';
import { Box, Typography, Avatar, Tooltip, Chip } from '@mui/material';
import { SmartToy, Person } from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark-dimmed.css';
import { useCruseStore } from '@/store/cruseStore';
import { TypingIndicator } from '@/components/chat/TypingIndicator';
import { WelcomeHero } from '@/components/landing/WelcomeHero';

function formatTimestamp(ts: number): string {
  const diff = Math.floor((Date.now() - ts) / 1000);
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return new Date(ts).toLocaleDateString();
}

export function ChatPanel() {
  const messages = useCruseStore((s) => s.messages);
  const isStreaming = useCruseStore((s) => s.isStreaming);
  const streamingContent = useCruseStore((s) => s.streamingContent);
  const darkMode = useCruseStore((s) => s.darkMode);
  const sessionId = useCruseStore((s) => s.sessionId);
  const sampleQueries = useCruseStore((s) => s.sampleQueries);
  const setPendingInput = useCruseStore((s) => s.setPendingInput);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streamingContent, isStreaming]);

  if (!sessionId) {
    return <WelcomeHero />;
  }

  return (
    <Box
      ref={scrollRef}
      sx={{
        flex: 1,
        overflow: 'auto',
        p: { xs: 1, md: 2 },
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      {messages.length === 0 && !isStreaming && (
        <Box
          sx={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
            gap: 2,
          }}
        >
          <SmartToy sx={{ fontSize: 48, opacity: 0.3 }} />
          <Typography variant="body1" sx={{ opacity: 0.4 }}>
            {sampleQueries.length > 0 ? 'Try one of these to get started' : 'Send a message to get started'}
          </Typography>
          {sampleQueries.length > 0 && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center', maxWidth: { xs: '90%', md: 500 } }}>
              {sampleQueries.map((query, i) => (
                <motion.div
                  key={query}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.1, type: 'spring', stiffness: 300, damping: 20 }}
                  style={{ maxWidth: '100%' }}
                >
                  <Chip
                    label={query}
                    variant="outlined"
                    color="primary"
                    onClick={() => setPendingInput(query)}
                    sx={{
                      maxWidth: '100%',
                      height: 'auto',
                      '& .MuiChip-label': {
                        whiteSpace: 'normal',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      },
                      cursor: 'pointer',
                      '&:hover': {
                        bgcolor: 'primary.main',
                        color: 'white',
                        borderColor: 'primary.main',
                      },
                      transition: 'all 0.2s ease',
                    }}
                  />
                </motion.div>
              ))}
            </Box>
          )}
        </Box>
      )}

      <AnimatePresence initial={false}>
        {messages.map((msg) => (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Box
              sx={{
                display: 'flex',
                gap: 1.5,
                alignItems: 'flex-start',
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
              }}
            >
              <Avatar
                sx={{
                  width: 32,
                  height: 32,
                  bgcolor: msg.role === 'user' ? 'primary.main' : 'secondary.main',
                  fontSize: 16,
                }}
              >
                {msg.role === 'user' ? <Person fontSize="small" /> : <SmartToy fontSize="small" />}
              </Avatar>

              <Tooltip
                title={formatTimestamp(msg.timestamp)}
                placement={msg.role === 'user' ? 'left' : 'right'}
                arrow
              >
                <Box
                  sx={{
                    maxWidth: { xs: '90%', md: '80%' },
                    minWidth: 0,
                    px: 2,
                    py: 1.5,
                    borderRadius: 2,
                    bgcolor: msg.role === 'user'
                      ? 'primary.main'
                      : darkMode
                        ? 'rgba(255,255,255,0.06)'
                        : 'rgba(0,0,0,0.04)',
                    color: msg.role === 'user' ? 'white' : 'text.primary',
                  }}
                >
                  {msg.role === 'user' ? (
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'break-word', wordBreak: 'break-word' }}>
                      {msg.content}
                    </Typography>
                  ) : (
                    <Box className="markdown-content" sx={{ '& > *:last-child': { mb: 0 }, overflowWrap: 'break-word', wordBreak: 'break-word', overflow: 'hidden' }}>
                      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
                        {msg.content}
                      </ReactMarkdown>
                    </Box>
                  )}
                </Box>
              </Tooltip>
            </Box>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Streaming content */}
      {isStreaming && streamingContent && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start' }}>
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main', fontSize: 16 }}>
              <SmartToy fontSize="small" />
            </Avatar>
            <Box
              sx={{
                maxWidth: { xs: '90%', md: '80%' },
                minWidth: 0,
                px: 2,
                py: 1.5,
                borderRadius: 2,
                bgcolor: darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)',
              }}
            >
              <Box className="markdown-content" sx={{ overflowWrap: 'break-word', wordBreak: 'break-word', overflow: 'hidden' }}>
                <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
                  {streamingContent}
                </ReactMarkdown>
              </Box>
            </Box>
          </Box>
        </motion.div>
      )}

      {/* Typing indicator */}
      {isStreaming && !streamingContent && <TypingIndicator />}
    </Box>
  );
}
