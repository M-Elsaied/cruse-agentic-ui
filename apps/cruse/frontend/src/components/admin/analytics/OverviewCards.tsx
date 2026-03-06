'use client';

import { Box, Card, CardContent, Chip, Typography } from '@mui/material';
import type { AnalyticsOverview } from './useAnalytics';

interface OverviewCardsProps {
  overview: AnalyticsOverview;
  darkMode: boolean;
}

function pctChange(current: number, previous: number): number | null {
  if (previous === 0) return current > 0 ? 100 : null;
  return Math.round(((current - previous) / previous) * 100);
}

function formatNumber(n: number): string {
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return n.toString();
}

function ChangeBadge({ change }: { change: number | null }) {
  if (change === null) return null;
  const isPositive = change >= 0;
  return (
    <Chip
      label={`${isPositive ? '+' : ''}${change}%`}
      size="small"
      sx={{
        height: 18,
        fontSize: '0.6rem',
        fontWeight: 700,
        bgcolor: isPositive ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
        color: isPositive ? '#22c55e' : '#ef4444',
        '& .MuiChip-label': { px: 0.75 },
      }}
    />
  );
}

interface KpiCardProps {
  label: string;
  value: string;
  change: number | null;
  darkMode: boolean;
  invertChange?: boolean;
}

function KpiCard({ label, value, change, darkMode, invertChange }: KpiCardProps) {
  const displayChange = invertChange && change !== null ? -change : change;
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
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>
            {label}
          </Typography>
          <ChangeBadge change={displayChange} />
        </Box>
        <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '1.1rem' }}>
          {value}
        </Typography>
      </CardContent>
    </Card>
  );
}

export function OverviewCards({ overview, darkMode }: OverviewCardsProps) {
  const cards = [
    {
      label: 'Total Requests',
      value: formatNumber(overview.total_requests),
      change: pctChange(overview.total_requests, overview.prev_total_requests),
    },
    {
      label: 'Active Users',
      value: formatNumber(overview.unique_users),
      change: pctChange(overview.unique_users, overview.prev_unique_users),
    },
    {
      label: 'Avg Latency',
      value: overview.avg_latency_ms > 0 ? `${Math.round(overview.avg_latency_ms)}ms` : '—',
      change: null,
    },
    {
      label: 'Error Rate',
      value: `${(overview.error_rate * 100).toFixed(1)}%`,
      change: pctChange(overview.error_rate, overview.prev_error_rate),
      invertChange: true,
    },
    {
      label: 'Satisfaction',
      value: overview.satisfaction_score >= 0 ? `${Math.round(overview.satisfaction_score * 100)}%` : '—',
      change: null,
    },
    {
      label: 'Open Reports',
      value: overview.open_reports.toString(),
      change: null,
    },
  ];

  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 1 }}>
      {cards.map((c) => (
        <KpiCard
          key={c.label}
          label={c.label}
          value={c.value}
          change={c.change ?? null}
          darkMode={darkMode}
          invertChange={'invertChange' in c ? c.invertChange : false}
        />
      ))}
    </Box>
  );
}
