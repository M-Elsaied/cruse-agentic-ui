'use client';

import { Box, Typography } from '@mui/material';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { ActiveUsersPoint } from './useAnalytics';

interface ActiveUsersChartProps {
  data: ActiveUsersPoint[];
  darkMode: boolean;
}

export function ActiveUsersChart({ data, darkMode }: ActiveUsersChartProps) {
  if (data.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 3 }}>
        <Typography variant="body2" color="text.secondary">No user data</Typography>
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
        Daily Active Users
      </Typography>
      <ResponsiveContainer width="100%" height={150}>
        <LineChart data={formatted} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
          <XAxis dataKey="label" tick={{ fontSize: 10, fill: textColor }} tickLine={false} />
          <YAxis tick={{ fontSize: 10, fill: textColor }} tickLine={false} axisLine={false} allowDecimals={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: darkMode ? '#1e293b' : '#fff',
              border: 'none',
              borderRadius: 8,
              fontSize: 12,
            }}
          />
          <Line type="monotone" dataKey="count" name="Users" stroke="#8b5cf6" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </Box>
  );
}
