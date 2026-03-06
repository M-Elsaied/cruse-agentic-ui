'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemText,
  Typography,
} from '@mui/material';
import { Close, Delete as DeleteIcon } from '@mui/icons-material';
import { useCruseStore } from '@/store/cruseStore';
import { useAuthenticatedFetch } from '@/utils/api';
import type { ConversationDetail, ConversationSummary } from '@/types/history';

const DRAWER_WIDTH = 420;
const PAGE_SIZE = 50;

function formatRelativeDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return 'This Week';
  return date.toLocaleDateString();
}

function groupByDate(conversations: ConversationSummary[]): [string, ConversationSummary[]][] {
  const groups: Record<string, ConversationSummary[]> = {};
  for (const conv of conversations) {
    const label = formatRelativeDate(conv.updated_at);
    if (!groups[label]) groups[label] = [];
    groups[label].push(conv);
  }
  return Object.entries(groups);
}

function formatNetworkName(name: string): string {
  const base = name.split('/').pop() || name;
  return base.replace(/\.hocon$/, '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function HistoryDrawer() {
  const open = useCruseStore((s) => s.historyDrawerOpen);
  const toggleDrawer = useCruseStore((s) => s.toggleHistoryDrawer);
  const conversations = useCruseStore((s) => s.conversationHistory);
  const setConversations = useCruseStore((s) => s.setConversationHistory);
  const loading = useCruseStore((s) => s.historyLoading);
  const setLoading = useCruseStore((s) => s.setHistoryLoading);
  const setViewingConversation = useCruseStore((s) => s.setViewingConversation);
  const darkMode = useCruseStore((s) => s.darkMode);
  const { authFetch, API_BASE } = useAuthenticatedFetch();
  const [hasMore, setHasMore] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState<number | null>(null);

  const fetchConversations = useCallback(
    async (offset = 0) => {
      setLoading(true);
      try {
        const res = await authFetch(
          `${API_BASE}/api/conversations?limit=${PAGE_SIZE}&offset=${offset}`,
        );
        if (!res.ok) return;
        const data = await res.json();
        if (offset === 0) {
          setConversations(data.conversations);
        } else {
          // Read current state directly to avoid stale closure on rapid pagination
          const current = useCruseStore.getState().conversationHistory;
          setConversations([...current, ...data.conversations]);
        }
        setHasMore(data.has_more);
      } catch {
        // Silently fail — user can retry
      } finally {
        setLoading(false);
      }
    },
    [authFetch, API_BASE, setLoading, setConversations],
  );

  useEffect(() => {
    if (open) {
      fetchConversations(0);
    }
    // Only fetch when drawer opens, not on every dependency change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const handleSelect = useCallback(
    async (convId: number) => {
      setLoadingDetail(convId);
      try {
        const res = await authFetch(`${API_BASE}/api/conversations/${convId}`);
        if (!res.ok) return;
        const data: ConversationDetail = await res.json();
        setViewingConversation(data);
        toggleDrawer();
      } catch {
        // Silently fail
      } finally {
        setLoadingDetail(null);
      }
    },
    [authFetch, API_BASE, setViewingConversation, toggleDrawer],
  );

  const handleArchive = useCallback(
    async (e: React.MouseEvent, convId: number) => {
      e.stopPropagation();
      try {
        const res = await authFetch(`${API_BASE}/api/conversations/${convId}`, {
          method: 'DELETE',
        });
        if (res.ok) {
          const current = useCruseStore.getState().conversationHistory;
          setConversations(current.filter((c) => c.id !== convId));
        }
      } catch {
        // Silently fail
      }
    },
    [authFetch, API_BASE, setConversations],
  );

  const grouped = groupByDate(conversations);

  return (
    <Drawer
      anchor="right"
      variant="temporary"
      open={open}
      onClose={toggleDrawer}
      ModalProps={{ keepMounted: true }}
      PaperProps={{
        sx: {
          width: DRAWER_WIDTH,
          maxWidth: '90vw',
          bgcolor: darkMode ? 'rgba(15, 23, 42, 0.92)' : 'rgba(248, 250, 252, 0.92)',
          backdropFilter: 'blur(20px)',
          borderLeft: '1px solid',
          borderColor: darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          px: 2,
          py: 1.5,
          borderBottom: '1px solid',
          borderColor: darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
        }}
      >
        <Typography variant="subtitle1" sx={{ fontWeight: 700, flex: 1 }}>
          Conversation History
        </Typography>
        <IconButton size="small" onClick={toggleDrawer}>
          <Close fontSize="small" />
        </IconButton>
      </Box>

      {/* Content */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {loading && conversations.length === 0 ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress size={28} />
          </Box>
        ) : conversations.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4, px: 2 }}>
            <Typography variant="body2" sx={{ opacity: 0.5 }}>
              No conversations yet
            </Typography>
          </Box>
        ) : (
          <List disablePadding>
            {grouped.map(([dateLabel, convs]) => (
              <Box key={dateLabel}>
                <Typography
                  variant="caption"
                  sx={{
                    px: 2,
                    py: 0.75,
                    display: 'block',
                    fontWeight: 600,
                    opacity: 0.5,
                    textTransform: 'uppercase',
                    letterSpacing: 0.5,
                  }}
                >
                  {dateLabel}
                </Typography>
                {convs.map((conv) => (
                  <ListItemButton
                    key={conv.id}
                    onClick={() => handleSelect(conv.id)}
                    disabled={loadingDetail === conv.id}
                    sx={{
                      px: 2,
                      py: 1,
                      '&:hover .history-delete': { opacity: 1 },
                    }}
                  >
                    <ListItemText
                      primary={conv.title || 'Untitled'}
                      secondary={
                        <Box component="span" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.25 }}>
                          <Chip
                            label={formatNetworkName(conv.agent_network)}
                            size="small"
                            variant="outlined"
                            sx={{ height: 20, fontSize: '0.7rem' }}
                          />
                          <Typography component="span" variant="caption" sx={{ opacity: 0.5 }}>
                            {conv.message_count} message{conv.message_count !== 1 ? 's' : ''}
                          </Typography>
                        </Box>
                      }
                      primaryTypographyProps={{
                        variant: 'body2',
                        noWrap: true,
                        sx: { fontWeight: 500 },
                      }}
                    />
                    {loadingDetail === conv.id ? (
                      <CircularProgress size={18} sx={{ ml: 1 }} />
                    ) : (
                      <IconButton
                        className="history-delete"
                        size="small"
                        onClick={(e) => handleArchive(e, conv.id)}
                        sx={{ opacity: 0, transition: 'opacity 0.2s' }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    )}
                  </ListItemButton>
                ))}
              </Box>
            ))}
          </List>
        )}

        {hasMore && (
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <Button
              size="small"
              onClick={() => fetchConversations(conversations.length)}
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Load More'}
            </Button>
          </Box>
        )}
      </Box>
    </Drawer>
  );
}