'use client';

import { Suspense, useMemo } from 'react';
import * as MuiIcons from '@mui/icons-material';
import { SvgIcon } from '@mui/material';

interface DynamicIconProps {
  name?: string;
  color?: string;
  size?: number;
}

/**
 * Resolves a Material Design icon by PascalCase name string.
 * Falls back to a generic icon if the name is not found.
 */
export function DynamicIcon({ name, color, size = 28 }: DynamicIconProps) {
  const IconComponent = useMemo(() => {
    if (!name) return MuiIcons.AutoAwesome;

    // Try exact match
    const icons = MuiIcons as Record<string, typeof SvgIcon>;
    if (icons[name]) return icons[name];

    // Try with "Outlined" suffix
    if (icons[`${name}Outlined`]) return icons[`${name}Outlined`];

    // Try with "Rounded" suffix
    if (icons[`${name}Rounded`]) return icons[`${name}Rounded`];

    return MuiIcons.AutoAwesome;
  }, [name]);

  return (
    <Suspense fallback={<MuiIcons.AutoAwesome sx={{ fontSize: size, color }} />}>
      <IconComponent sx={{ fontSize: size, color }} />
    </Suspense>
  );
}
