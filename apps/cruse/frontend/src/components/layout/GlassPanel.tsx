'use client';

import { Box } from '@mui/material';
import type { SxProps, Theme } from '@mui/material';
import type { ReactNode } from 'react';

interface GlassPanelProps {
  children: ReactNode;
  sx?: SxProps<Theme>;
}

/**
 * Reusable frosted glass container component.
 * Applies backdrop-filter blur with semi-transparent background.
 */
export function GlassPanel({ children, sx }: GlassPanelProps) {
  return (
    <Box
      className="glass-panel"
      sx={{
        borderRadius: 4,
        overflow: 'hidden',
        ...sx,
      }}
    >
      {children}
    </Box>
  );
}
