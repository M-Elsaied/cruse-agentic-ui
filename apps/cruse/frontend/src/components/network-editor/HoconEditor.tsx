'use client';

import { useCallback, useRef } from 'react';
import Editor, { type OnMount } from '@monaco-editor/react';
import { Box } from '@mui/material';
import { useCruseStore } from '@/store/cruseStore';

interface HoconEditorProps {
  value: string;
  onChange: (value: string) => void;
  readOnly?: boolean;
  height?: string | number;
}

export function HoconEditor({ value, onChange, readOnly = false, height = '400px' }: HoconEditorProps) {
  const darkMode = useCruseStore((s) => s.darkMode);
  const editorRef = useRef<Parameters<OnMount>[0] | null>(null);

  const handleMount: OnMount = useCallback((editor) => {
    editorRef.current = editor;
  }, []);

  return (
    <Box
      sx={{
        border: '1px solid',
        borderColor: darkMode ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.12)',
        borderRadius: 1,
        overflow: 'hidden',
      }}
    >
      <Editor
        height={height}
        language="json"
        theme={darkMode ? 'vs-dark' : 'light'}
        value={value}
        onChange={(v) => onChange(v || '')}
        onMount={handleMount}
        options={{
          readOnly,
          minimap: { enabled: false },
          fontSize: 13,
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          wordWrap: 'on',
          automaticLayout: true,
          tabSize: 2,
          folding: true,
          renderLineHighlight: 'line',
        }}
      />
    </Box>
  );
}
