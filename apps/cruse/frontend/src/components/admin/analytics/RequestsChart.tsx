'use client';

import { Box, Typography } from '@mui/material';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { TimeSeriesPoint } from './useAnalytics';

interface RequestsChartProps {
  data: TimeSeriesPoint[];
  darkMode: boolean;
}

export function RequestsChart({ data, darkMode }: RequestsChartProps) {
  if (data.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 3 }}>
        <Typography variant="body2" color="text.secondary">No request data</Typography>
      </Box>
    );
  }

  const textColor = darkMode ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.5)';
  const gridColor = darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';

  const formatted = data.map((d) => ({
    ...d,
    label: d.date.slice(5),
  }));

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
        Requests Over Time
      </Typography>
      <ResponsiveContainer width="100%" height={180}>
        <AreaChart data={formatted} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="reqFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="errFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
          <XAxis dataKey="label" tick={{ fontSize: 10, fill: textColor }} tickLine={false} />
          <YAxis tick={{ fontSize: 10, fill: textColor }} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: darkMode ? '#1e293b' : '#fff',
              border: 'none',
              borderRadius: 8,
              fontSize: 12,
            }}
          />
          <Area type="monotone" dataKey="count" name="Requests" stroke="#3b82f6" fill="url(#reqFill)" strokeWidth={2} />
          <Area type="monotone" dataKey="error_count" name="Errors" stroke="#ef4444" fill="url(#errFill)" strokeWidth={1.5} />
        </AreaChart>
      </ResponsiveContainer>
    </Box>
  );
}
