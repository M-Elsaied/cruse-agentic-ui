'use client';

import { useCallback, useState } from 'react';
import { Box, Typography, Chip, FormHelperText } from '@mui/material';
import { CloudUpload, InsertDriveFile } from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import type { WidgetProps } from '@rjsf/utils';

export function FileUploadField(props: WidgetProps) {
  const { id, onChange, schema, label, rawErrors } = props;
  const [files, setFiles] = useState<File[]>([]);

  const uiHints = (schema as any)?.['x-ui'] || {};
  const accept = uiHints.accept || '';
  const maxFiles = uiHints.maxFiles || 1;
  const maxSize = uiHints.maxSize || 26214400;

  const acceptObj: Record<string, string[]> = {};
  if (accept) {
    accept.split(',').forEach((ext: string) => {
      const trimmed = ext.trim();
      // Map extensions to MIME types (simplified)
      if (trimmed === '.pdf') acceptObj['application/pdf'] = ['.pdf'];
      else if (trimmed === '.doc' || trimmed === '.docx')
        acceptObj['application/msword'] = ['.doc', '.docx'];
      else if (['.jpg', '.jpeg', '.png'].includes(trimmed))
        acceptObj['image/*'] = ['.jpg', '.jpeg', '.png'];
      else if (trimmed === '.csv') acceptObj['text/csv'] = ['.csv'];
      else if (trimmed === '.txt') acceptObj['text/plain'] = ['.txt'];
      else if (trimmed === '.json') acceptObj['application/json'] = ['.json'];
    });
  }

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      setFiles(acceptedFiles);
      // Convert to file names for the form value
      if (maxFiles === 1 && acceptedFiles.length > 0) {
        onChange(acceptedFiles[0].name);
      } else {
        onChange(acceptedFiles.map((f) => f.name));
      }
    },
    [maxFiles, onChange]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles,
    maxSize,
    accept: Object.keys(acceptObj).length > 0 ? acceptObj : undefined,
  });

  const removeFile = (index: number) => {
    const updated = files.filter((_, i) => i !== index);
    setFiles(updated);
    if (maxFiles === 1) {
      onChange(updated.length > 0 ? updated[0].name : undefined);
    } else {
      onChange(updated.map((f) => f.name));
    }
  };

  return (
    <Box>
      <Typography variant="body2" gutterBottom>
        {label}
      </Typography>
      <Box
        {...getRootProps()}
        id={id}
        sx={{
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'divider',
          borderRadius: 2,
          p: 3,
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.2s',
          bgcolor: isDragActive ? 'action.hover' : 'transparent',
          '&:hover': { borderColor: 'primary.main', bgcolor: 'action.hover' },
        }}
      >
        <input {...getInputProps()} />
        <CloudUpload sx={{ fontSize: 36, opacity: 0.4, mb: 1 }} />
        <Typography variant="body2" color="text.secondary">
          {isDragActive ? 'Drop files here' : 'Drag & drop files here, or click to browse'}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Max {maxFiles} file{maxFiles > 1 ? 's' : ''}, up to{' '}
          {Math.round(maxSize / 1024 / 1024)}MB each
        </Typography>
      </Box>

      {files.length > 0 && (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
          {files.map((file, i) => (
            <Chip
              key={i}
              icon={<InsertDriveFile />}
              label={file.name}
              size="small"
              onDelete={() => removeFile(i)}
            />
          ))}
        </Box>
      )}

      {rawErrors && rawErrors.length > 0 && (
        <FormHelperText error>{rawErrors.join(', ')}</FormHelperText>
      )}
    </Box>
  );
}
