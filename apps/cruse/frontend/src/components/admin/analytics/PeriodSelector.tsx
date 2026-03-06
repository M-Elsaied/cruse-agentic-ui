'use client';

import { ToggleButton, ToggleButtonGroup } from '@mui/material';

interface PeriodSelectorProps {
  value: number;
  onChange: (days: number) => void;
}

const PERIODS = [
  { label: '7d', value: 7 },
  { label: '30d', value: 30 },
  { label: '90d', value: 90 },
];

export function PeriodSelector({ value, onChange }: PeriodSelectorProps) {
  return (
    <ToggleButtonGroup
      value={value}
      exclusive
      onChange={(_, v) => v !== null && onChange(v)}
      size="small"
      sx={{
        '& .MuiToggleButton-root': {
          px: 1.5,
          py: 0.25,
          fontSize: '0.7rem',
          textTransform: 'none',
        },
      }}
    >
      {PERIODS.map((p) => (
        <ToggleButton key={p.value} value={p.value}>
          {p.label}
        </ToggleButton>
      ))}
    </ToggleButtonGroup>
  );
}
