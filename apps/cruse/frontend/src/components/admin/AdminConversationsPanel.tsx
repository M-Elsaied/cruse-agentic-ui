'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Chip,
  CircularProgress,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material';
import { ArrowBack, ExpandMore } from '@mui/icons-material';
import { useAuthenticatedFetch } from '@/utils/api';
import { useCruseStore } from '@/store/cruseStore';

interface AdminConversation {
  id: number;
  session_id: string;
  agent_network: string;
  title: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  message_count: number;
  user_id: string;
  user_email: string | null;
  user_name: string | null;
}

interface ConversationMessage {
  id: number;
  role: string;
  content: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

interface ConversationDetail {
  conversation: {
    id: number;
    session_id: string;
    agent_network: string;
    title: string | null;
    created_at: string;
    message_count: number;
  };
  messages: ConversationMessage[];
}

function timeAgo(dateStr: string): string {
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function networkLabel(network: string): string {
  return network.split('/').pop()?.replace(/_/g, ' ') || network;
}

function userDisplay(conv: AdminConversation): string {
  if (conv.user_name) return conv.user_name;
  if (conv.user_email) return conv.user_email;
  return conv.user_id.slice(0, 12) + '...';
}

export function AdminConversationsPanel() {
  const { authFetch, API_BASE } = useAuthenticatedFetch();
  const darkMode = useCruseStore((s) => s.darkMode);
  const adminDrawerOpen = useCruseStore((s) => s.adminDrawerOpen);

  // List state
  const [conversations, setConversations] = useState<AdminConversation[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  // Detail state
  const [selectedConv, setSelectedConv] = useState<AdminConversation | null>(null);
  const [detail, setDetail] = useState<ConversationDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const fetchConversations = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: String(rowsPerPage),
        offset: String(page * rowsPerPage),
        include_archived: 'true',
      });
      const res = await authFetch(`${API_BASE}/api/admin/conversations?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setConversations(data.conversations);
        setTotal(data.total);
      }
    } catch {
      // Best-effort
    } finally {
      setLoading(false);
    }
  }, [authFetch, API_BASE, page, rowsPerPage]);

  useEffect(() => {
    if (adminDrawerOpen && !selectedConv) {
      fetchConversations();
    }
  }, [adminDrawerOpen, fetchConversations, selectedConv]);

  const openDetail = async (conv: AdminConversation) => {
    setSelectedConv(conv);
    setDetailLoading(true);
    try {
      const res = await authFetch(`${API_BASE}/api/conversations/${conv.id}`);
      if (res.ok) {
        setDetail(await res.json());
      }
    } catch {
      // Best-effort
    } finally {
      setDetailLoading(false);
    }
  };

  const goBack = () => {
    setSelectedConv(null);
    setDetail(null);
  };

  // ─── Detail View ───────────────────────────────────────────
  if (selectedConv) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
        {/* Header */}
        <Box
          sx={{
            px: 1.5,
            py: 1,
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            borderBottom: '1px solid',
            borderColor: darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
          }}
        >
          <IconButton size="small" onClick={goBack}>
            <ArrowBack fontSize="small" />
          </IconButton>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography variant="subtitle2" noWrap sx={{ fontWeight: 600 }}>
              {selectedConv.title || 'Untitled'}
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.6 }}>
              {userDisplay(selectedConv)} &middot; {networkLabel(selectedConv.agent_network)}
            </Typography>
          </Box>
        </Box>

        {/* Messages */}
        <Box sx={{ flex: 1, overflow: 'auto', p: 1.5 }}>
          {detailLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress size={24} />
            </Box>
          ) : detail ? (
            detail.messages.map((msg) => (
              <Box
                key={msg.id}
                sx={{
                  mb: 1.5,
                  p: 1.5,
                  borderRadius: 1.5,
                  bgcolor:
                    msg.role === 'user'
                      ? darkMode
                        ? 'rgba(59, 130, 246, 0.08)'
                        : 'rgba(59, 130, 246, 0.04)'
                      : darkMode
                        ? 'rgba(255,255,255,0.04)'
                        : 'rgba(0,0,0,0.02)',
                  border: '1px solid',
                  borderColor: darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                  <Chip
                    label={msg.role}
                    size="small"
                    color={msg.role === 'user' ? 'primary' : 'default'}
                    variant="outlined"
                    sx={{ height: 20, fontSize: '0.65rem', textTransform: 'capitalize' }}
                  />
                  {msg.metadata?.latency_ms != null && (
                    <Typography variant="caption" sx={{ opacity: 0.5 }}>
                      {String(msg.metadata.latency_ms)}ms
                    </Typography>
                  )}
                  <Typography variant="caption" sx={{ opacity: 0.4, ml: 'auto' }}>
                    {new Date(msg.created_at).toLocaleTimeString()}
                  </Typography>
                </Box>
                <Typography
                  variant="body2"
                  sx={{
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    fontSize: '0.8rem',
                    lineHeight: 1.5,
                  }}
                >
                  {msg.content}
                </Typography>

                {/* Agent trace accordion (admin-only metadata) */}
                {msg.metadata?.agent_trace && (
                  <Accordion
                    disableGutters
                    elevation={0}
                    sx={{
                      mt: 1,
                      bgcolor: 'transparent',
                      '&:before': { display: 'none' },
                      border: '1px solid',
                      borderColor: darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
                      borderRadius: '8px !important',
                    }}
                  >
                    <AccordionSummary expandIcon={<ExpandMore fontSize="small" />} sx={{ minHeight: 32 }}>
                      <Typography variant="caption" sx={{ fontWeight: 600, opacity: 0.7 }}>
                        Agent Trace ({(msg.metadata.agent_trace as unknown[]).length} entries)
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails sx={{ pt: 0 }}>
                      <Box
                        component="pre"
                        sx={{
                          fontSize: '0.7rem',
                          overflow: 'auto',
                          maxHeight: 300,
                          m: 0,
                          p: 1,
                          borderRadius: 1,
                          bgcolor: darkMode ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.04)',
                        }}
                      >
                        {JSON.stringify(msg.metadata.agent_trace, null, 2)}
                      </Box>
                    </AccordionDetails>
                  </Accordion>
                )}
              </Box>
            ))
          ) : (
            <Typography variant="body2" sx={{ opacity: 0.5, textAlign: 'center', py: 4 }}>
              Failed to load conversation
            </Typography>
          )}
        </Box>
      </Box>
    );
  }

  // ─── List View ─────────────────────────────────────────────
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
      <Box sx={{ px: 2, py: 1, display: 'flex', alignItems: 'center' }}>
        <Typography variant="caption" sx={{ opacity: 0.6 }}>
          {total} conversation{total !== 1 ? 's' : ''}
        </Typography>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress size={24} />
        </Box>
      ) : conversations.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body2" color="text.secondary">
            No conversations found
          </Typography>
        </Box>
      ) : (
        <>
          <TableContainer sx={{ flex: 1, overflow: 'auto' }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 700, fontSize: '0.7rem' }}>User</TableCell>
                  <TableCell sx={{ fontWeight: 700, fontSize: '0.7rem' }}>Network</TableCell>
                  <TableCell sx={{ fontWeight: 700, fontSize: '0.7rem' }}>Title</TableCell>
                  <TableCell sx={{ fontWeight: 700, fontSize: '0.7rem' }} align="center">
                    Msgs
                  </TableCell>
                  <TableCell sx={{ fontWeight: 700, fontSize: '0.7rem' }}>Updated</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {conversations.map((conv) => (
                  <TableRow
                    key={conv.id}
                    hover
                    onClick={() => openDetail(conv)}
                    sx={{ cursor: 'pointer' }}
                  >
                    <TableCell sx={{ fontSize: '0.72rem', maxWidth: 130, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      <Tooltip title={conv.user_email || conv.user_id}>
                        <span>{userDisplay(conv)}</span>
                      </Tooltip>
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.72rem' }}>
                      {networkLabel(conv.agent_network)}
                    </TableCell>
                    <TableCell
                      sx={{
                        fontSize: '0.72rem',
                        maxWidth: 140,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {conv.title || '—'}
                    </TableCell>
                    <TableCell align="center" sx={{ fontSize: '0.72rem' }}>
                      {conv.message_count}
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.72rem' }}>
                      {timeAgo(conv.updated_at)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            component="div"
            count={total}
            page={page}
            onPageChange={(_, p) => setPage(p)}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10));
              setPage(0);
            }}
            rowsPerPageOptions={[10, 25, 50]}
            sx={{ borderTop: '1px solid', borderColor: darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }}
          />
        </>
      )}
    </Box>
  );
}
