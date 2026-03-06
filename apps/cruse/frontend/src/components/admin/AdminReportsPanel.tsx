'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  Box,
  Chip,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Typography,
} from '@mui/material';
import { useAuthenticatedFetch } from '@/utils/api';
import { useCruseStore } from '@/store/cruseStore';

interface Report {
  id: number;
  category: string;
  body: string;
  status: string;
  created_at: string;
}

const categoryColors: Record<string, 'error' | 'info' | 'default'> = {
  bug: 'error',
  feature: 'info',
  general: 'default',
};

export function AdminReportsPanel() {
  const { authFetch, API_BASE } = useAuthenticatedFetch();
  const darkMode = useCruseStore((s) => s.darkMode);
  const adminDrawerOpen = useCruseStore((s) => s.adminDrawerOpen);
  const [reports, setReports] = useState<Report[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('');

  const fetchReports = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set('status', statusFilter);
      const res = await authFetch(`${API_BASE}/api/admin/reports?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setReports(data.reports);
        setTotal(data.total);
      }
    } catch {
      // Best-effort
    } finally {
      setLoading(false);
    }
  }, [authFetch, API_BASE, statusFilter]);

  useEffect(() => {
    if (adminDrawerOpen) {
      fetchReports();
    }
  }, [adminDrawerOpen, fetchReports]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
      <Box sx={{ px: 2, py: 1.5, display: 'flex', alignItems: 'center', gap: 1 }}>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Status</InputLabel>
          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            label="Status"
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="open">Open</MenuItem>
            <MenuItem value="resolved">Resolved</MenuItem>
          </Select>
        </FormControl>
        <Typography variant="caption" sx={{ opacity: 0.6, ml: 'auto' }}>
          {total} report{total !== 1 ? 's' : ''}
        </Typography>
      </Box>

      <Box sx={{ flex: 1, overflow: 'auto', px: 2 }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress size={24} />
          </Box>
        ) : reports.length === 0 ? (
          <Typography variant="body2" sx={{ opacity: 0.5, textAlign: 'center', py: 4 }}>
            No reports found
          </Typography>
        ) : (
          reports.map((report) => (
            <Box
              key={report.id}
              sx={{
                mb: 1.5,
                p: 1.5,
                borderRadius: 1.5,
                bgcolor: darkMode ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.02)',
                border: '1px solid',
                borderColor: darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <Chip
                  label={report.category}
                  size="small"
                  color={categoryColors[report.category] || 'default'}
                  variant="outlined"
                  sx={{ textTransform: 'capitalize', height: 22, fontSize: '0.7rem' }}
                />
                <Chip
                  label={report.status}
                  size="small"
                  variant="filled"
                  sx={{
                    height: 22,
                    fontSize: '0.7rem',
                    bgcolor: report.status === 'open'
                      ? (darkMode ? 'rgba(59, 130, 246, 0.2)' : 'rgba(59, 130, 246, 0.1)')
                      : (darkMode ? 'rgba(34, 197, 94, 0.2)' : 'rgba(34, 197, 94, 0.1)'),
                  }}
                />
                <Typography variant="caption" sx={{ opacity: 0.5, ml: 'auto' }}>
                  {new Date(report.created_at).toLocaleDateString()}
                </Typography>
              </Box>
              <Typography
                variant="body2"
                sx={{
                  whiteSpace: 'pre-wrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  display: '-webkit-box',
                  WebkitLineClamp: 3,
                  WebkitBoxOrient: 'vertical',
                }}
              >
                {report.body}
              </Typography>
            </Box>
          ))
        )}
      </Box>
    </Box>
  );
}