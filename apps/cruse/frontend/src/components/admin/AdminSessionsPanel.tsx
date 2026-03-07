'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  Box,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
  CircularProgress,
} from '@mui/material';
import { DeleteOutline } from '@mui/icons-material';
import { useAuthenticatedFetch } from '@/utils/api';

interface SessionEntry {
  session_id: string;
  agent_network: string;
  user_id: string;
  email: string | null;
  name: string | null;
  created_at: number;
}

const POLL_INTERVAL = 30000;

function timeAgo(ts: number): string {
  const seconds = Math.floor((Date.now() / 1000) - ts);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}

export function AdminSessionsPanel() {
  const [sessions, setSessions] = useState<SessionEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const { authFetch, API_BASE } = useAuthenticatedFetch();

  const fetchSessions = useCallback(async () => {
    try {
      const res = await authFetch(`${API_BASE}/api/admin/sessions`);
      const data = await res.json();
      setSessions(data.sessions || []);
    } catch (err) {
      console.error('Failed to fetch admin sessions:', err);
    } finally {
      setLoading(false);
    }
  }, [authFetch, API_BASE]);

  useEffect(() => {
    fetchSessions();
    const interval = setInterval(fetchSessions, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchSessions]);

  const destroySession = async (sessionId: string) => {
    try {
      await authFetch(`${API_BASE}/api/admin/session/${sessionId}`, { method: 'DELETE' });
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
    } catch (err) {
      console.error('Failed to destroy session:', err);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  if (sessions.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="body2" color="text.secondary">
          No active sessions
        </Typography>
      </Box>
    );
  }

  return (
    <TableContainer sx={{ maxHeight: '100%' }}>
      <Table size="small" stickyHeader>
        <TableHead>
          <TableRow>
            <TableCell sx={{ fontWeight: 700, fontSize: '0.75rem' }}>User</TableCell>
            <TableCell sx={{ fontWeight: 700, fontSize: '0.75rem' }}>Network</TableCell>
            <TableCell sx={{ fontWeight: 700, fontSize: '0.75rem' }}>Created</TableCell>
            <TableCell sx={{ fontWeight: 700, fontSize: '0.75rem' }} align="right">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {sessions.map((s) => (
            <TableRow key={s.session_id} hover>
              <TableCell sx={{ fontSize: '0.75rem', maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                <Tooltip title={s.email || s.user_id}>
                  <span>{s.name || s.email || `${s.user_id.slice(0, 12)}...`}</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontSize: '0.75rem' }}>
                {s.agent_network.split('/').pop()?.replace(/_/g, ' ')}
              </TableCell>
              <TableCell sx={{ fontSize: '0.75rem' }}>
                {timeAgo(s.created_at)}
              </TableCell>
              <TableCell align="right">
                <Tooltip title="Destroy session">
                  <IconButton size="small" onClick={() => destroySession(s.session_id)}>
                    <DeleteOutline fontSize="small" color="error" />
                  </IconButton>
                </Tooltip>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
