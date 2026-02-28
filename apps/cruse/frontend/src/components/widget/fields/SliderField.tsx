'use client';

import { Box, Slider, Typography, FormHelperText } from '@mui/material';
import type { WidgetProps } from '@rjsf/utils';

export function SliderField(props: WidgetProps) {
  const { id, value, onChange, schema, label, rawErrors } = props;
  const min = schema.minimum ?? 0;
  const max = schema.maximum ?? 100;
  const step = schema.multipleOf ?? 1;

  return (
    <Box sx={{ px: 1 }}>
      <Typography variant="body2" gutterBottom>
        {label}
      </Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Typography variant="caption" color="text.secondary">
          {min}
        </Typography>
        <Slider
          id={id}
          value={value ?? min}
          onChange={(_, val) => onChange(val)}
          min={min}
          max={max}
          step={step}
          valueLabelDisplay="auto"
          sx={{ flex: 1 }}
        />
        <Typography variant="caption" color="text.secondary">
          {max}
        </Typography>
      </Box>
      {rawErrors && rawErrors.length > 0 && (
        <FormHelperText error>{rawErrors.join(', ')}</FormHelperText>
      )}
    </Box>
  );
}
