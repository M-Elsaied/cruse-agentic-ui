'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  Box,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  Typography,
} from '@mui/material';
import { useAuthenticatedFetch } from '@/utils/api';
import type { UserBreakdown, UserBreakdownData } from './useAnalytics';

interface UserBreakdownTableProps {
  periodDays: number;
  darkMode: boolean;
}

export function UserBreakdownTable({ periodDays, darkMode }: UserBreakdownTableProps) {
  const [data, setData] = useState<UserBreakdownData | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const { authFetch, API_BASE } = useAuthenticatedFetch();

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const offset = page * rowsPerPage;
      const res = await authFetch(
        `${API_BASE}/api/admin/analytics/users?period_days=${periodDays}&limit=${rowsPerPage}&offset=${offset}`
      );
      if (res.ok) {
        setData(await res.json());
      }
    } catch {
      // best-effort
    } finally {
      setLoading(false);
    }
  }, [authFetch, API_BASE, periodDays, page, rowsPerPage]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const cellSx = { fontSize: '0.7rem', py: 0.75, px: 1 };
  const headerSx = { ...cellSx, fontWeight: 700, opacity: 0.7 };

  function formatTime(iso: string | null): string {
    if (!iso) return '—';
    const diff = Date.now() - new Date(iso).getTime();
    const hours = Math.floor(diff / 3600000);
    if (hours < 1) return 'just now';
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
        User Breakdown
      </Typography>
      {loading && !data ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
          <CircularProgress size={20} />
        </Box>
      ) : !data || data.users.length === 0 ? (
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 3 }}>
          No user data
        </Typography>
      ) : (
        <>
          <TableContainer sx={{ maxHeight: 300 }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell sx={headerSx}>User</TableCell>
                  <TableCell sx={headerSx} align="right">Requests</TableCell>
                  <TableCell sx={headerSx} align="right">Conversations</TableCell>
                  <TableCell sx={headerSx} align="right">Latency</TableCell>
                  <TableCell sx={headerSx} align="right">Last Active</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.users.map((u: UserBreakdown) => (
                  <TableRow
                    key={u.user_id}
                    sx={{
                      '&:hover': {
                        bgcolor: darkMode ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
                      },
                    }}
                  >
                    <TableCell sx={cellSx}>
                      {u.email || u.name || u.user_id.slice(0, 12) + '...'}
                    </TableCell>
                    <TableCell sx={cellSx} align="right">{u.request_count}</TableCell>
                    <TableCell sx={cellSx} align="right">{u.conversation_count}</TableCell>
                    <TableCell sx={cellSx} align="right">
                      {u.avg_latency_ms > 0 ? `${Math.round(u.avg_latency_ms)}ms` : '—'}
                    </TableCell>
                    <TableCell sx={cellSx} align="right">{formatTime(u.last_active)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            component="div"
            count={data.total}
            page={page}
            onPageChange={(_, p) => setPage(p)}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10));
              setPage(0);
            }}
            rowsPerPageOptions={[10, 25, 50]}
            sx={{ '& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': { fontSize: '0.7rem' } }}
          />
        </>
      )}
    </Box>
  );
}
