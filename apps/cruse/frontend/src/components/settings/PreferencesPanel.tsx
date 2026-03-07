'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Button,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
  Alert,
  Chip,
  Tooltip,
} from '@mui/material';
import { Info as InfoIcon } from '@mui/icons-material';
import { useAuthenticatedFetch } from '@/utils/api';
import type { PreferenceResponse } from '@/types/settings';

export function PreferencesPanel() {
  const { authFetch, API_BASE } = useAuthenticatedFetch();
  const [provider, setProvider] = useState('');
  const [model, setModel] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchPrefs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await authFetch(`${API_BASE}/api/settings/preferences`);
      const data: PreferenceResponse = await res.json();
      setProvider(data.preferred_provider || '');
      setModel(data.preferred_model || '');
    } catch {
      console.error('Failed to fetch preferences');
    } finally {
      setLoading(false);
    }
  }, [authFetch, API_BASE]);

  useEffect(() => {
    fetchPrefs();
  }, [fetchPrefs]);

  const handleSave = async () => {
    setSaving(true);
    setFeedback(null);
    try {
      const res = await authFetch(`${API_BASE}/api/settings/preferences`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          preferred_provider: provider || null,
          preferred_model: model || null,
        }),
      });
      if (res.ok) {
        setFeedback({ type: 'success', message: 'Preferences saved' });
      } else {
        setFeedback({ type: 'error', message: 'Failed to save preferences' });
      }
    } catch {
      setFeedback({ type: 'error', message: 'Network error' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress size={32} />
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Chip label="Beta" size="small" color="warning" variant="outlined" />
        <Tooltip title="Model preferences will take effect when custom networks are available (coming soon). Currently, all sessions use the platform model configuration.">
          <InfoIcon fontSize="small" color="action" sx={{ cursor: 'help' }} />
        </Tooltip>
      </Box>

      <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
        <Typography variant="body2">
          These preferences are saved but <strong>not yet active</strong>. They will take effect
          when per-user network configuration is available in a future update.
        </Typography>
      </Alert>

      {feedback && (
        <Alert severity={feedback.type} onClose={() => setFeedback(null)} sx={{ borderRadius: 2 }}>
          {feedback.message}
        </Alert>
      )}

      <FormControl fullWidth size="small">
        <InputLabel>Preferred Provider</InputLabel>
        <Select
          value={provider}
          label="Preferred Provider"
          onChange={(e) => setProvider(e.target.value)}
        >
          <MenuItem value="">Auto (use network default)</MenuItem>
          <MenuItem value="openai">OpenAI</MenuItem>
          <MenuItem value="anthropic">Anthropic</MenuItem>
          <MenuItem value="google">Google</MenuItem>
        </Select>
      </FormControl>

      <TextField
        fullWidth
        size="small"
        label="Preferred Model"
        placeholder="e.g., gpt-4o, claude-sonnet-4-20250514"
        value={model}
        onChange={(e) => setModel(e.target.value)}
      />

      <Button
        variant="contained"
        onClick={handleSave}
        disabled={saving}
        startIcon={saving ? <CircularProgress size={16} /> : undefined}
        sx={{ alignSelf: 'flex-start' }}
      >
        {saving ? 'Saving...' : 'Save Preferences'}
      </Button>
    </Box>
  );
}
