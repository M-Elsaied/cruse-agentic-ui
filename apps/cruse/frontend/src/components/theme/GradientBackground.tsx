'use client';

import { useMemo } from 'react';
import { Box } from '@mui/material';
import type { GradientTheme } from '@/types/theme';

interface GradientBackgroundProps {
  theme: GradientTheme;
}

export function GradientBackground({ theme }: GradientBackgroundProps) {
  const cssGradient = useMemo(() => {
    const stops = theme.colors.map((c) => `${c.color} ${c.stop}`).join(', ');

    switch (theme.mode) {
      case 'radial':
        return `radial-gradient(${theme.shape || 'circle'}, ${stops})`;
      case 'conic':
        return `conic-gradient(${stops})`;
      case 'linear':
      default:
        return `linear-gradient(${theme.angle || '135deg'}, ${stops})`;
    }
  }, [theme]);

  return (
    <Box
      sx={{
        position: 'absolute',
        inset: 0,
        background: cssGradient,
        zIndex: 0,
        transition: 'background 1s ease-in-out',
      }}
    />
  );
}
