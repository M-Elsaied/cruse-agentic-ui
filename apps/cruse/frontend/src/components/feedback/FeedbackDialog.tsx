'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  FormControlLabel,
  Switch,
  Snackbar,
  Alert,
  Box,
} from '@mui/material';
import { useCruseStore } from '@/store/cruseStore';
import { useAuthenticatedFetch } from '@/utils/api';

export function FeedbackDialog() {
  const open = useCruseStore((s) => s.feedbackDialogOpen);
  const targetMessage = useCruseStore((s) => s.feedbackTargetMessage);
  const closeFeedbackDialog = useCruseStore((s) => s.closeFeedbackDialog);
  const setFeedbackRating = useCruseStore((s) => s.setFeedbackRating);
  const agentNetwork = useCruseStore((s) => s.agentNetwork);
  const sessionId = useCruseStore((s) => s.sessionId);
  const darkMode = useCruseStore((s) => s.darkMode);
  const { authFetch, API_BASE } = useAuthenticatedFetch();

  const [comment, setComment] = useState('');
  const [isReport, setIsReport] = useState(false);
  const [category, setCategory] = useState('bug');
  const [reportBody, setReportBody] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; severity: 'success' | 'error'; message: string }>({
    open: false,
    severity: 'success',
    message: '',
  });

  const handleClose = () => {
    closeFeedbackDialog();
    setComment('');
    setIsReport(false);
    setCategory('bug');
    setReportBody('');
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      // Submit rating comment if we have a target message
      if (targetMessage?.dbId && comment) {
        setFeedbackRating(targetMessage.id, -1);
        await authFetch(`${API_BASE}/api/messages/${targetMessage.dbId}/rating`, {
          method: 'POST',
          body: JSON.stringify({ rating: -1, comment }),
        });
      }

      // Submit report if toggled
      if (isReport && reportBody.trim()) {
        // Find the conversation_id from the viewing context or current session
        const viewingConversation = useCruseStore.getState().viewingConversation;
        const conversationId = viewingConversation?.conversation.id ?? null;

        await authFetch(`${API_BASE}/api/reports`, {
          method: 'POST',
          body: JSON.stringify({
            body: reportBody,
            category,
            conversation_id: conversationId,
            message_id: targetMessage?.dbId ?? null,
          }),
        });
      }

      setSnackbar({ open: true, severity: 'success', message: 'Thanks for your feedback!' });
      handleClose();
    } catch {
      setSnackbar({ open: true, severity: 'error', message: 'Failed to submit feedback' });
    } finally {
      setSubmitting(false);
    }
  };

  const canSubmit = comment.trim() || (isReport && reportBody.trim());

  return (
    <>
      <Dialog
        open={open}
        onClose={handleClose}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            bgcolor: darkMode ? 'rgba(15, 23, 42, 0.95)' : 'rgba(255, 255, 255, 0.98)',
            backdropFilter: 'blur(20px)',
          },
        }}
      >
        <DialogTitle sx={{ fontWeight: 700 }}>Send Feedback</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="What went wrong? (optional)"
              multiline
              rows={2}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              fullWidth
              size="small"
              placeholder="This response was inaccurate because..."
            />

            <FormControlLabel
              control={<Switch checked={isReport} onChange={(e) => setIsReport(e.target.checked)} size="small" />}
              label="Report an issue"
            />

            {isReport && (
              <>
                <FormControl size="small" fullWidth>
                  <InputLabel>Category</InputLabel>
                  <Select value={category} onChange={(e) => setCategory(e.target.value)} label="Category">
                    <MenuItem value="bug">Bug</MenuItem>
                    <MenuItem value="feature">Feature Request</MenuItem>
                    <MenuItem value="general">General</MenuItem>
                  </Select>
                </FormControl>

                <TextField
                  label="Describe the issue"
                  multiline
                  rows={4}
                  value={reportBody}
                  onChange={(e) => setReportBody(e.target.value)}
                  fullWidth
                  size="small"
                  required
                  placeholder="Please describe what happened and what you expected..."
                />

                {agentNetwork && (
                  <Box sx={{ fontSize: '0.75rem', opacity: 0.5 }}>
                    Context: {agentNetwork}{sessionId ? ` (session: ${sessionId.slice(0, 8)}...)` : ''}
                  </Box>
                )}
              </>
            )}
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleClose} size="small">
            Cancel
          </Button>
          <Button onClick={handleSubmit} variant="contained" size="small" disabled={!canSubmit || submitting}>
            {submitting ? 'Submitting...' : 'Submit'}
          </Button>
        </DialogActions>
      </Dialog>

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