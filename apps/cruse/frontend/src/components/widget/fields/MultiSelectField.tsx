'use client';

import { Autocomplete, Chip, TextField } from '@mui/material';
import type { WidgetProps } from '@rjsf/utils';

export function MultiSelectField(props: WidgetProps) {
  const { id, value, onChange, schema, label } = props;

  const options: string[] = (schema as any)?.items?.enum || [];

  return (
    <Autocomplete
      id={id}
      multiple
      options={options}
      value={value || []}
      onChange={(_, newValue) => onChange(newValue)}
      renderTags={(tagValue, getTagProps) =>
        tagValue.map((option, index) => (
          <Chip
            {...getTagProps({ index })}
            key={option}
            label={option}
            size="small"
            color="primary"
            variant="outlined"
          />
        ))
      }
      renderInput={(params) => (
        <TextField
          {...params}
          label={label}
          size="small"
          placeholder="Select options..."
        />
      )}
    />
  );
}
