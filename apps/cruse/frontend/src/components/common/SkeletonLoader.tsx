'use client';

import { Box, Skeleton } from '@mui/material';

export function ChatSkeleton() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, p: 2 }}>
      {[1, 2, 3].map((i) => (
        <Box key={i} sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start' }}>
          <Skeleton variant="circular" width={32} height={32} />
          <Box sx={{ flex: 1, maxWidth: '70%' }}>
            <Skeleton variant="rounded" height={60} sx={{ borderRadius: 2 }} />
          </Box>
        </Box>
      ))}
    </Box>
  );
}

export function WidgetSkeleton() {
  return (
    <Box sx={{ p: 2 }}>
      <Skeleton variant="rounded" height={60} sx={{ borderRadius: '16px 16px 0 0', mb: 0 }} />
      <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Skeleton variant="rounded" height={40} />
        <Skeleton variant="rounded" height={40} />
        <Skeleton variant="rounded" height={40} />
        <Skeleton variant="rounded" height={36} width={120} />
      </Box>
    </Box>
  );
}
