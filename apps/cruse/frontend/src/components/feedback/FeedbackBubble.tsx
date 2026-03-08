'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  ClickAwayListener,
  Grow,
  Snackbar,
  TextField,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import { Feedback as FeedbackIcon, Close as CloseIcon } from '@mui/icons-material';
import { useCruseStore } from '@/store/cruseStore';
import { useAuthenticatedFetch } from '@/utils/api';

const categories = [
  { value: 'bug', label: 'Bug', icon: '🐛' },
  { value: 'feature', label: 'Feature', icon: '✨' },
  { value: 'general', label: 'General', icon: '💬' },
] as const;

const FAB_SIZE = 48;
const FAB_SIZE_MOBILE = 40;
const EDGE_MARGIN = 12;

export function FeedbackBubble() {
  const darkMode = useCruseStore((s) => s.darkMode);
  const agentNetwork = useCruseStore((s) => s.agentNetwork);
  const sessionId = useCruseStore((s) => s.sessionId);
  const { authFetch, API_BASE } = useAuthenticatedFetch();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState<string>('bug');
  const [body, setBody] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; severity: 'success' | 'error'; message: string }>({
    open: false,
    severity: 'success',
    message: '',
  });

  // Drag state
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null);
  const dragging = useRef(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const posStart = useRef({ x: 0, y: 0 });
  const hasMoved = useRef(false);
  const fabRef = useRef<HTMLButtonElement>(null);

  // Set default position once on mount (bottom-left, above input bar)
  useEffect(() => {
    const size = isMobile ? FAB_SIZE_MOBILE : FAB_SIZE;
    setPos({
      x: EDGE_MARGIN,
      y: window.innerHeight - size - (isMobile ? 80 : 90),
    });
  }, [isMobile]);

  const clampPos = useCallback((x: number, y: number) => {
    const size = isMobile ? FAB_SIZE_MOBILE : FAB_SIZE;
    return {
      x: Math.max(EDGE_MARGIN, Math.min(x, window.innerWidth - size - EDGE_MARGIN)),
      y: Math.max(EDGE_MARGIN, Math.min(y, window.innerHeight - size - EDGE_MARGIN)),
    };
  }, [isMobile]);

  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    if (open) return; // Don't drag when panel is open
    dragging.current = true;
    hasMoved.current = false;
    dragStart.current = { x: e.clientX, y: e.clientY };
    posStart.current = pos ?? { x: 0, y: 0 };
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }, [open, pos]);

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!dragging.current) return;
    const dx = e.clientX - dragStart.current.x;
    const dy = e.clientY - dragStart.current.y;
    if (Math.abs(dx) > 4 || Math.abs(dy) > 4) {
      hasMoved.current = true;
    }
    setPos(clampPos(posStart.current.x + dx, posStart.current.y + dy));
  }, [clampPos]);

  const handlePointerUp = useCallback(() => {
    dragging.current = false;
  }, []);

  const handleClick = useCallback(() => {
    if (hasMoved.current) return; // Was a drag, not a click
    setOpen((prev) => {
      if (prev) {
        setBody('');
        setCategory('bug');
      }
      return !prev;
    });
  }, []);

  const reset = useCallback(() => {
    setBody('');
    setCategory('bug');
  }, []);

  const handleSubmit = async () => {
    if (!body.trim()) return;
    setSubmitting(true);
    try {
      const viewingConversation = useCruseStore.getState().viewingConversation;
      const conversationId = viewingConversation?.conversation.id ?? null;

      const res = await authFetch(`${API_BASE}/api/reports`, {
        method: 'POST',
        body: JSON.stringify({
          body: body.trim(),
          category,
          conversation_id: conversationId,
        }),
      });
      if (res.ok) {
        setSnackbar({ open: true, severity: 'success', message: 'Thanks for your feedback!' });
        reset();
        setOpen(false);
      } else {
        const err = await res.json().catch(() => ({ detail: 'Submission failed' }));
        setSnackbar({ open: true, severity: 'error', message: err.detail || 'Failed to submit' });
      }
    } catch {
      setSnackbar({ open: true, severity: 'error', message: 'Failed to submit feedback' });
    } finally {
      setSubmitting(false);
    }
  };

  const panelBg = darkMode ? 'rgba(15, 23, 42, 0.97)' : 'rgba(255, 255, 255, 0.98)';
  const borderColor = darkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)';

  if (!pos) return null;

  // Panel position: above/below and left/right of FAB depending on where it is
  const fabSize = isMobile ? FAB_SIZE_MOBILE : FAB_SIZE;
  const panelWidth = isMobile ? Math.min(340, window.innerWidth - 24) : 360;
  const panelOnRight = pos.x < window.innerWidth / 2;
  const panelOnTop = pos.y > window.innerHeight / 2;

  const panelStyle: React.CSSProperties = {
    position: 'fixed',
    width: panelWidth,
    zIndex: 1201,
    ...(panelOnRight
      ? { left: pos.x }
      : { right: window.innerWidth - pos.x - fabSize }),
    ...(panelOnTop
      ? { bottom: window.innerHeight - pos.y + 8 }
      : { top: pos.y + fabSize + 8 }),
  };

  return (
    <>
      {/* Draggable FAB */}
      <Box
        component="button"
        ref={fabRef}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onClick={handleClick}
        sx={{
          position: 'fixed',
          left: pos.x,
          top: pos.y,
          width: fabSize,
          height: fabSize,
          borderRadius: '50%',
          border: 'none',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: dragging.current ? 'grabbing' : 'grab',
          zIndex: 1200,
          touchAction: 'none',
          bgcolor: open
            ? (darkMode ? 'rgba(239, 68, 68, 0.9)' : '#ef4444')
            : (darkMode ? 'rgba(59, 130, 246, 0.85)' : '#3b82f6'),
          color: '#fff',
          '&:hover': {
            bgcolor: open
              ? (darkMode ? 'rgba(220, 38, 38, 0.95)' : '#dc2626')
              : (darkMode ? 'rgba(37, 99, 235, 0.9)' : '#2563eb'),
          },
          transition: dragging.current ? 'none' : 'background-color 0.2s ease',
          boxShadow: open ? '0 2px 8px rgba(0,0,0,0.2)' : '0 4px 20px rgba(59, 130, 246, 0.4)',
        }}
      >
        {open ? <CloseIcon /> : <FeedbackIcon />}
      </Box>

      {/* Feedback Panel */}
      <Grow in={open} style={{ transformOrigin: panelOnTop ? 'bottom left' : 'top left' }}>
        <Box
          sx={{
            ...panelStyle,
            maxHeight: isMobile ? '70vh' : 480,
            borderRadius: 3,
            overflow: 'hidden',
            bgcolor: panelBg,
            backdropFilter: 'blur(24px)',
            border: `1px solid ${borderColor}`,
            boxShadow: darkMode
              ? '0 16px 48px rgba(0,0,0,0.5)'
              : '0 16px 48px rgba(0,0,0,0.12)',
            display: open ? 'flex' : 'none',
            flexDirection: 'column',
          }}
        >
          <ClickAwayListener
            onClickAway={(e) => {
              if (fabRef.current?.contains(e.target as Node)) return;
              if (open && !body.trim()) {
                setOpen(false);
                reset();
              }
            }}
          >
            <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              {/* Header */}
              <Box sx={{ px: 2.5, pt: 2, pb: 1 }}>
                <Typography variant="subtitle1" fontWeight={700}>
                  Send Feedback
                </Typography>
                <Typography variant="caption" sx={{ opacity: 0.5 }}>
                  Help us improve your experience
                </Typography>
              </Box>

              {/* Category chips */}
              <Box sx={{ px: 2.5, pb: 1.5, display: 'flex', gap: 1 }}>
                {categories.map((cat) => (
                  <Button
                    key={cat.value}
                    size="small"
                    variant={category === cat.value ? 'contained' : 'outlined'}
                    onClick={() => setCategory(cat.value)}
                    sx={{
                      flex: 1,
                      borderRadius: 2,
                      textTransform: 'none',
                      fontSize: '0.8rem',
                      fontWeight: category === cat.value ? 700 : 500,
                      py: 0.75,
                      minWidth: 0,
                      ...(category === cat.value
                        ? {
                            bgcolor: darkMode ? 'rgba(59, 130, 246, 0.3)' : '#3b82f6',
                            color: darkMode ? '#93c5fd' : '#fff',
                            borderColor: 'transparent',
                            '&:hover': {
                              bgcolor: darkMode ? 'rgba(59, 130, 246, 0.4)' : '#2563eb',
                            },
                          }
                        : {
                            borderColor: darkMode ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.12)',
                            color: darkMode ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.6)',
                          }),
                    }}
                  >
                    {cat.icon}&nbsp;{cat.label}
                  </Button>
                ))}
              </Box>

              {/* Body input */}
              <Box sx={{ px: 2.5, flex: 1 }}>
                <TextField
                  placeholder={
                    category === 'bug'
                      ? 'Describe the bug you encountered...'
                      : category === 'feature'
                        ? 'What feature would you like to see?'
                        : 'Share your thoughts...'
                  }
                  multiline
                  rows={isMobile ? 3 : 4}
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  fullWidth
                  size="small"
                  inputProps={{ maxLength: 5000 }}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2,
                      fontSize: '0.875rem',
                    },
                  }}
                />
              </Box>

              {/* Context hint + submit */}
              <Box sx={{ px: 2.5, py: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                {agentNetwork && (
                  <Typography variant="caption" sx={{ opacity: 0.4, flex: 1, fontSize: '0.65rem' }}>
                    {agentNetwork}{sessionId ? ` / ${sessionId.slice(0, 8)}` : ''}
                  </Typography>
                )}
                <Box sx={{ ml: 'auto' }}>
                  <Button
                    variant="contained"
                    size="small"
                    onClick={handleSubmit}
                    disabled={!body.trim() || submitting}
                    sx={{
                      borderRadius: 2,
                      textTransform: 'none',
                      fontWeight: 600,
                      px: 3,
                    }}
                  >
                    {submitting ? 'Sending...' : 'Submit'}
                  </Button>
                </Box>
              </Box>
            </Box>
          </ClickAwayListener>
        </Box>
      </Grow>

      {/* Success/error snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity={snackbar.severity} variant="filled" sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  );
}
