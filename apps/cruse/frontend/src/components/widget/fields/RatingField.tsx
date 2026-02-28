'use client';

import { Box, Rating, Typography, FormHelperText } from '@mui/material';
import type { WidgetProps } from '@rjsf/utils';

export function RatingField(props: WidgetProps) {
  const { id, value, onChange, schema, label, rawErrors } = props;
  const max = schema.maximum ?? 5;

  return (
    <Box>
      <Typography variant="body2" gutterBottom>
        {label}
      </Typography>
      <Rating
        id={id}
        value={value ?? 0}
        onChange={(_, val) => onChange(val)}
        max={max}
        size="large"
      />
      {rawErrors && rawErrors.length > 0 && (
        <FormHelperText error>{rawErrors.join(', ')}</FormHelperText>
      )}
    </Box>
  );
}
