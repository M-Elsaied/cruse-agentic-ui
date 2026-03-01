'use client';

import { useCallback, useEffect, useState } from 'react';
import { Box, Card, CardContent, CircularProgress, Typography } from '@mui/material';
import { useAuthenticatedFetch } from '@/utils/api';
import { useCruseStore } from '@/store/cruseStore';

interface Stats {
  total_sessions: number;
  active_sessions: number;
  total_messages: number;
  sessions_by_user: Record<string, number>;
  sessions_by_network: Record<string, number>;
}

export function AdminStatsPanel() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const { authFetch, API_BASE } = useAuthenticatedFetch();
  const darkMode = useCruseStore((s) => s.darkMode);

  const fetchStats = useCallback(async () => {
    try {
      const res = await authFetch(`${API_BASE}/api/admin/stats`);
      const data = await res.json();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch admin stats:', err);
    } finally {
      setLoading(false);
    }
  }, [authFetch, API_BASE]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  if (!stats) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="body2" color="text.secondary">
          Failed to load statistics
        </Typography>
      </Box>
    );
  }

  const networkEntries = Object.entries(stats.sessions_by_network || {}).sort((a, b) => b[1] - a[1]);
  const maxCount = Math.max(...networkEntries.map(([, count]) => count), 1);

  return (
    <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
      {/* Summary cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 1.5 }}>
        <StatCard label="Total Sessions" value={stats.total_sessions} darkMode={darkMode} />
        <StatCard label="Active" value={stats.active_sessions} darkMode={darkMode} />
        <StatCard label="Messages" value={stats.total_messages} darkMode={darkMode} />
      </Box>

      {/* Sessions by network */}
      {networkEntries.length > 0 && (
        <Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
            Sessions by Network
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
            {networkEntries.map(([network, count]) => (
              <Box key={network} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="caption" sx={{ minWidth: 100, fontSize: '0.7rem' }}>
                  {network.split('/').pop()?.replace(/_/g, ' ')}
                </Typography>
                <Box sx={{ flex: 1, position: 'relative', height: 16, borderRadius: 1, overflow: 'hidden' }}>
                  <Box
                    sx={{
                      position: 'absolute',
                      inset: 0,
                      bgcolor: darkMode ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)',
                      borderRadius: 1,
                    }}
                  />
                  <Box
                    sx={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      bottom: 0,
                      width: `${(count / maxCount) * 100}%`,
                      background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
                      borderRadius: 1,
                    }}
                  />
                </Box>
                <Typography variant="caption" sx={{ minWidth: 20, textAlign: 'right', fontWeight: 600 }}>
                  {count}
                </Typography>
              </Box>
            ))}
          </Box>
        </Box>
      )}

      {/* Unique users */}
      <Typography variant="body2" color="text.secondary">
        {Object.keys(stats.sessions_by_user || {}).length} unique user(s)
      </Typography>
    </Box>
  );
}

function StatCard({ label, value, darkMode }: { label: string; value: number; darkMode: boolean }) {
  return (
    <Card
      variant="outlined"
      sx={{
        bgcolor: darkMode ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
        border: '1px solid',
        borderColor: darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
      }}
    >
      <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
          {label}
        </Typography>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>
          {value}
        </Typography>
      </CardContent>
    </Card>
  );
}
