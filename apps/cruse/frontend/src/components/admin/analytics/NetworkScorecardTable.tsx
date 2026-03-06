'use client';

import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import type { NetworkScorecard } from './useAnalytics';

interface NetworkScorecardTableProps {
  data: NetworkScorecard[];
  darkMode: boolean;
}

function formatNetwork(name: string): string {
  const short = name.split('/').pop() || name;
  return short.replace(/_/g, ' ');
}

export function NetworkScorecardTable({ data, darkMode }: NetworkScorecardTableProps) {
  if (data.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 3 }}>
        <Typography variant="body2" color="text.secondary">No network data</Typography>
      </Box>
    );
  }

  const cellSx = { fontSize: '0.7rem', py: 0.75, px: 1 };
  const headerSx = { ...cellSx, fontWeight: 700, opacity: 0.7 };

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
        Network Scorecard
      </Typography>
      <TableContainer sx={{ maxHeight: 300 }}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={headerSx}>Network</TableCell>
              <TableCell sx={headerSx} align="right">Requests</TableCell>
              <TableCell sx={headerSx} align="right">Latency</TableCell>
              <TableCell sx={headerSx} align="right">Errors</TableCell>
              <TableCell sx={headerSx} align="right">Satisfaction</TableCell>
              <TableCell sx={headerSx} align="right">Depth</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((row) => (
              <TableRow
                key={row.network}
                sx={{
                  '&:hover': {
                    bgcolor: darkMode ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
                  },
                }}
              >
                <TableCell sx={cellSx}>{formatNetwork(row.network)}</TableCell>
                <TableCell sx={cellSx} align="right">{row.request_count}</TableCell>
                <TableCell sx={cellSx} align="right">
                  {row.avg_latency_ms > 0 ? `${Math.round(row.avg_latency_ms)}ms` : '—'}
                </TableCell>
                <TableCell
                  sx={{
                    ...cellSx,
                    color: row.error_rate > 0.05 ? '#ef4444' : 'inherit',
                  }}
                  align="right"
                >
                  {(row.error_rate * 100).toFixed(1)}%
                </TableCell>
                <TableCell
                  sx={{
                    ...cellSx,
                    color: row.satisfaction_score >= 0
                      ? row.satisfaction_score >= 0.7 ? '#22c55e' : '#f59e0b'
                      : 'inherit',
                  }}
                  align="right"
                >
                  {row.satisfaction_score >= 0 ? `${Math.round(row.satisfaction_score * 100)}%` : '—'}
                </TableCell>
                <TableCell sx={cellSx} align="right">
                  {row.avg_depth > 0 ? row.avg_depth.toFixed(1) : '—'}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
