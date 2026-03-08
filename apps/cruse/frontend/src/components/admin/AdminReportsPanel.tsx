'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Collapse,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Snackbar,
  Typography,
} from '@mui/material';
import {
  BugReport as BugIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
} from '@mui/icons-material';
import { useAuthenticatedFetch } from '@/utils/api';
import { useCruseStore } from '@/store/cruseStore';

interface Report {
  id: number;
  category: string;
  body: string;
  status: string;
  created_at: string;
  user_id?: string;
  conversation_id?: number;
  message_id?: number;
  context?: {
    agent_network?: string;
    session_id?: string;
    agent_trace?: string;
  };
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
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [creatingIssue, setCreatingIssue] = useState<number | null>(null);
  const [snackbar, setSnackbar] = useState<string | null>(null);

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

  const handleCreateIssue = async (reportId: number) => {
    setCreatingIssue(reportId);
    try {
      const res = await authFetch(`${API_BASE}/api/admin/reports/${reportId}/github-issue`, {
        method: 'POST',
      });
      if (res.ok) {
        const data = await res.json();
        window.open(data.issue_url, '_blank');
        setSnackbar(`GitHub issue #${data.issue_number} created`);
      } else {
        const err = await res.json();
        setSnackbar(err.detail || 'Failed to create issue');
      }
    } catch {
      setSnackbar('Failed to create GitHub issue');
    } finally {
      setCreatingIssue(null);
    }
  };

  const metaChipSx = {
    height: 20,
    fontSize: '0.65rem',
    '& .MuiChip-label': { px: 0.75 },
  };

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
          reports.map((report) => {
            const isExpanded = expandedId === report.id;
            const hasContext = report.context && Object.keys(report.context).length > 0;

            return (
              <Box
                key={report.id}
                sx={{
                  mb: 1.5,
                  p: 1.5,
                  borderRadius: 1.5,
                  bgcolor: darkMode ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.02)',
                  border: '1px solid',
                  borderColor: darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
                  cursor: 'pointer',
                }}
                onClick={() => setExpandedId(isExpanded ? null : report.id)}
              >
                {/* Header row */}
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
                  {report.context?.agent_network && (
                    <Chip label={report.context.agent_network} size="small" variant="outlined" sx={metaChipSx} />
                  )}
                  <Typography variant="caption" sx={{ opacity: 0.5, ml: 'auto' }}>
                    {new Date(report.created_at).toLocaleDateString()}
                  </Typography>
                  {isExpanded ? <CollapseIcon fontSize="small" sx={{ opacity: 0.4 }} /> : <ExpandIcon fontSize="small" sx={{ opacity: 0.4 }} />}
                </Box>

                {/* Body preview */}
                <Typography
                  variant="body2"
                  sx={{
                    whiteSpace: 'pre-wrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    ...(!isExpanded && {
                      display: '-webkit-box',
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: 'vertical',
                    }),
                  }}
                >
                  {report.body}
                </Typography>

                {/* Expanded details */}
                <Collapse in={isExpanded}>
                  <Box sx={{ mt: 1.5, pt: 1.5, borderTop: '1px solid', borderColor: darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }}>
                    {/* Metadata grid */}
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1 }}>
                      {report.user_id && (
                        <MetaField label="User" value={report.user_id} darkMode={darkMode} />
                      )}
                      {report.context?.session_id && (
                        <MetaField label="Session" value={report.context.session_id} darkMode={darkMode} />
                      )}
                      {report.conversation_id && (
                        <MetaField label="Conversation" value={String(report.conversation_id)} darkMode={darkMode} />
                      )}
                      {report.message_id && (
                        <MetaField label="Message" value={String(report.message_id)} darkMode={darkMode} />
                      )}
                    </Box>

                    {/* Agent trace */}
                    {report.context?.agent_trace && (
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="caption" sx={{ opacity: 0.5, fontWeight: 600 }}>
                          Agent Trace
                        </Typography>
                        <Typography
                          variant="caption"
                          component="pre"
                          sx={{
                            mt: 0.5,
                            p: 1,
                            borderRadius: 1,
                            bgcolor: darkMode ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.04)',
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-all',
                            fontSize: '0.65rem',
                            maxHeight: 200,
                            overflow: 'auto',
                            display: 'block',
                          }}
                        >
                          {typeof report.context.agent_trace === 'string'
                            ? report.context.agent_trace
                            : JSON.stringify(report.context.agent_trace, null, 2)}
                        </Typography>
                      </Box>
                    )}

                    {/* Actions */}
                    <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={creatingIssue === report.id ? <CircularProgress size={14} /> : <BugIcon />}
                        disabled={creatingIssue === report.id}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCreateIssue(report.id);
                        }}
                      >
                        Create GitHub Issue
                      </Button>
                    </Box>
                  </Box>
                </Collapse>
              </Box>
            );
          })
        )}
      </Box>

      <Snackbar
        open={!!snackbar}
        autoHideDuration={4000}
        onClose={() => setSnackbar(null)}
        message={snackbar}
      />
    </Box>
  );
}

function MetaField({ label, value, darkMode }: { label: string; value: string; darkMode: boolean }) {
  return (
    <Box sx={{
      px: 1,
      py: 0.5,
      borderRadius: 1,
      bgcolor: darkMode ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)',
      minWidth: 0,
    }}>
      <Typography variant="caption" sx={{ opacity: 0.5, fontSize: '0.6rem', display: 'block' }}>
        {label}
      </Typography>
      <Typography variant="caption" sx={{ fontSize: '0.7rem', wordBreak: 'break-all' }}>
        {value}
      </Typography>
    </Box>
  );
}
