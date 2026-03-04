'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { Box, IconButton, TextField, Chip } from '@mui/material';
import { Send as SendIcon, Description as FormIcon } from '@mui/icons-material';
import { useCruseStore } from '@/store/cruseStore';
import { useWebSocket } from '@/hooks/useWebSocket';

/**
 * Scrape form data from the legacy HTML widget panel.
 * The WidgetCard wraps legacy HTML in <form id="cruse-legacy-form">,
 * mirroring the original Flask <form id="assistant-gui">.
 */
function scrapeLegacyFormData(): Record<string, unknown> | null {
  const form = document.getElementById('cruse-legacy-form') as HTMLFormElement | null;
  if (!form) return null;

  const fd = new FormData(form);
  const result: Record<string, unknown> = {};
  for (const [key, value] of fd.entries()) {
    result[key] = value;
  }
  return Object.keys(result).length > 0 ? result : null;
}

export function InputBar() {
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const isStreaming = useCruseStore((s) => s.isStreaming);
  const sessionId = useCruseStore((s) => s.sessionId);
  const widgetFormData = useCruseStore((s) => s.widgetFormData);
  const widgetSchema = useCruseStore((s) => s.widgetSchema);
  const pendingInput = useCruseStore((s) => s.pendingInput);
  const setPendingInput = useCruseStore((s) => s.setPendingInput);
  const setWidgetSubmitted = useCruseStore((s) => s.setWidgetSubmitted);
  const rateLimitRemaining = useCruseStore((s) => s.rateLimitRemaining);
  const rateLimitTotal = useCruseStore((s) => s.rateLimitTotal);
  const rateLimitExceeded = useCruseStore((s) => s.rateLimitExceeded);
  const { sendMessage } = useWebSocket();

  // Handle pending input from sample query chips
  useEffect(() => {
    if (pendingInput && sessionId && !isStreaming) {
      sendMessage(pendingInput);
      setPendingInput(null);
    }
  }, [pendingInput, sessionId, isStreaming, sendMessage, setPendingInput]);

  const isLegacyHtml = widgetSchema && '_html' in widgetSchema;

  const hasRjsfFormData = !isLegacyHtml && widgetSchema && Object.keys(widgetFormData).some(
    (k) => widgetFormData[k] !== undefined && widgetFormData[k] !== null && widgetFormData[k] !== ''
  );

  // For legacy HTML widgets, we always enable Send (we can't know form state
  // from React — we scrape on send, just like the original Flask app).
  const hasFormData = isLegacyHtml || hasRjsfFormData;

  const handleSend = useCallback(() => {
    const text = input.trim();
    if (!sessionId) return;
    if (isStreaming) return;

    let formData: Record<string, unknown> | undefined;

    if (isLegacyHtml) {
      // Scrape native HTML form elements from the DOM, just like the original
      // Flask sendUserInput() used new FormData(document.getElementById('assistant-gui'))
      const scraped = scrapeLegacyFormData();
      if (scraped) {
        formData = scraped;
      }
    } else if (hasRjsfFormData) {
      formData = widgetFormData;
    }

    // Need either text or form data to send
    if (!text && !formData) return;

    const messageText = text || '<form submitted>';
    sendMessage(messageText, formData);
    if (formData) {
      setWidgetSubmitted(true);
    }
    setInput('');
    inputRef.current?.focus();
  }, [input, isStreaming, sessionId, sendMessage, isLegacyHtml, hasRjsfFormData, widgetFormData, setWidgetSubmitted]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Box
      data-tour="input-bar"
      sx={{
        p: { xs: 1, md: 2 },
        borderTop: '1px solid',
        borderColor: 'divider',
        display: 'flex',
        gap: 1,
        alignItems: 'flex-end',
      }}
    >
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 0.5 }}>
        {rateLimitRemaining !== null && rateLimitTotal !== null && (
          <Chip
            label={
              rateLimitRemaining <= 0
                ? `No requests left today. Resets at ${new Date(new Date().setUTCHours(24, 0, 0, 0)).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}.`
                : `${rateLimitRemaining} request${rateLimitRemaining === 1 ? '' : 's'} left today`
            }
            size="small"
            color={rateLimitRemaining <= 5 ? 'warning' : 'default'}
            variant="outlined"
            sx={{ alignSelf: 'flex-start' }}
          />
        )}
        {hasFormData && (
          <Chip
            icon={<FormIcon />}
            label={isLegacyHtml
              ? 'Form choices will be sent with your message'
              : 'Form data will be sent with your message'
            }
            size="small"
            color="primary"
            variant="outlined"
            sx={{ alignSelf: 'flex-start' }}
          />
        )}
        <TextField
          inputRef={inputRef}
          fullWidth
          multiline
          maxRows={4}
          placeholder={
            rateLimitExceeded
              ? 'Daily request limit reached. Please try again tomorrow.'
              : sessionId
                ? hasFormData
                  ? 'Add a message (optional) and press Send to submit the form...'
                  : 'Type your message...'
                : 'Select an agent network first'
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={!sessionId || isStreaming || rateLimitExceeded}
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: 3,
            },
          }}
        />
      </Box>
      <IconButton
        color="primary"
        onClick={handleSend}
        disabled={(!input.trim() && !hasFormData) || isStreaming || !sessionId || rateLimitExceeded}
        sx={{
          bgcolor: 'primary.main',
          color: 'white',
          width: 44,
          height: 44,
          '&:hover': { bgcolor: 'primary.dark' },
          '&:disabled': { bgcolor: 'action.disabledBackground' },
        }}
      >
        <SendIcon fontSize="small" />
      </IconButton>
    </Box>
  );
}
