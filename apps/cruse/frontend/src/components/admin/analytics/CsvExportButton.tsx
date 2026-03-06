'use client';

import { useState } from 'react';
import { Button } from '@mui/material';
import { Download } from '@mui/icons-material';
import { useAuthenticatedFetch } from '@/utils/api';

interface CsvExportButtonProps {
  periodDays: number;
}

export function CsvExportButton({ periodDays }: CsvExportButtonProps) {
  const [loading, setLoading] = useState(false);
  const { authFetch, API_BASE } = useAuthenticatedFetch();

  const handleExport = async () => {
    setLoading(true);
    try {
      const res = await authFetch(`${API_BASE}/api/admin/analytics/export?period_days=${periodDays}`);
      if (!res.ok) return;
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'request_log_export.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // best-effort
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button
      variant="outlined"
      size="small"
      startIcon={<Download />}
      onClick={handleExport}
      disabled={loading}
      sx={{ textTransform: 'none', fontSize: '0.75rem' }}
    >
      {loading ? 'Exporting...' : 'Export CSV'}
    </Button>
  );
}
