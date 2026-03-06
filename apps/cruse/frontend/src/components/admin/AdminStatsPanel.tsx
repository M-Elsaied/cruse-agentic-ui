'use client';

import { Box, CircularProgress, Typography } from '@mui/material';
import { useCruseStore } from '@/store/cruseStore';
import { useAnalytics } from '@/components/admin/analytics/useAnalytics';
import { PeriodSelector } from '@/components/admin/analytics/PeriodSelector';
import { OverviewCards } from '@/components/admin/analytics/OverviewCards';
import { RequestsChart } from '@/components/admin/analytics/RequestsChart';
import { ActiveUsersChart } from '@/components/admin/analytics/ActiveUsersChart';
import { NetworkScorecardTable } from '@/components/admin/analytics/NetworkScorecardTable';
import { UserBreakdownTable } from '@/components/admin/analytics/UserBreakdownTable';
import { CsvExportButton } from '@/components/admin/analytics/CsvExportButton';

export function AdminStatsPanel() {
  const darkMode = useCruseStore((s) => s.darkMode);
  const { data, loading, error, periodDays, setPeriodDays } = useAnalytics();

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  if (error || !data) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="body2" color="text.secondary">
          {error || 'Failed to load analytics'}
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 2.5, overflow: 'auto', flex: 1 }}>
      {/* Period selector */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
          Analytics
        </Typography>
        <PeriodSelector value={periodDays} onChange={setPeriodDays} />
      </Box>

      {/* KPI cards */}
      <OverviewCards overview={data.overview} darkMode={darkMode} />

      {/* Charts */}
      <RequestsChart data={data.requests_over_time} darkMode={darkMode} />
      <ActiveUsersChart data={data.active_users_over_time} darkMode={darkMode} />

      {/* Network scorecard */}
      <NetworkScorecardTable data={data.network_scorecard} darkMode={darkMode} />

      {/* User breakdown */}
      <UserBreakdownTable periodDays={periodDays} darkMode={darkMode} />

      {/* Export */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
        <CsvExportButton periodDays={periodDays} />
      </Box>
    </Box>
  );
}
