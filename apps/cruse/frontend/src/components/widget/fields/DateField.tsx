'use client';

import { Box, Typography, FormHelperText } from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import dayjs from 'dayjs';
import type { WidgetProps } from '@rjsf/utils';

export function DateField(props: WidgetProps) {
  const { id, value, onChange, schema, label, rawErrors } = props;

  const uiHints = (schema as any)?.['x-ui'] || {};
  const minDate = uiHints.minDate ? dayjs(uiHints.minDate) : undefined;
  const maxDate = uiHints.maxDate ? dayjs(uiHints.maxDate) : undefined;

  return (
    <Box>
      <Typography variant="body2" gutterBottom>
        {label}
      </Typography>
      <DatePicker
        value={value ? dayjs(value) : null}
        onChange={(val) => onChange(val ? val.format('YYYY-MM-DD') : undefined)}
        minDate={minDate}
        maxDate={maxDate}
        slotProps={{
          textField: {
            id,
            size: 'small',
            fullWidth: true,
            error: rawErrors && rawErrors.length > 0,
          },
        }}
      />
      {rawErrors && rawErrors.length > 0 && (
        <FormHelperText error>{rawErrors.join(', ')}</FormHelperText>
      )}
    </Box>
  );
}
