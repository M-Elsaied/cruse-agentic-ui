'use client';

import { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  IconButton,
  InputAdornment,
  TextField,
  Typography,
  Alert,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Delete as DeleteIcon,
  CheckCircle,
  Cancel,
  Add as AddIcon,
} from '@mui/icons-material';
import { useCruseStore } from '@/store/cruseStore';
import { useAuthenticatedFetch } from '@/utils/api';
import type { KeyInfo, KeyListResponse, KeyStoreResponse } from '@/types/settings';

const PROVIDER_LABELS: Record<string, string> = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  google: 'Google',
};

export function ApiKeysPanel() {
  const { authFetch, API_BASE } = useAuthenticatedFetch();
  const apiKeys = useCruseStore((s) => s.apiKeys);
  const setApiKeys = useCruseStore((s) => s.setApiKeys);
  const hasByok = useCruseStore((s) => s.hasByok);
  const keySource = useCruseStore((s) => s.keySource);
  const setHasByok = useCruseStore((s) => s.setHasByok);
  const setKeySource = useCruseStore((s) => s.setKeySource);
  const darkMode = useCruseStore((s) => s.darkMode);

  const [supportedProviders, setSupportedProviders] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [addingProvider, setAddingProvider] = useState<string | null>(null);
  const [keyInput, setKeyInput] = useState('');
  const [labelInput, setLabelInput] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchKeys = useCallback(async () => {
    setLoading(true);
    try {
      const res = await authFetch(`${API_BASE}/api/settings/keys`);
      const data: KeyListResponse = await res.json();
      setApiKeys(data.keys);
      setSupportedProviders(data.supported_providers);
    } catch {
      console.error('Failed to fetch keys');
    } finally {
      setLoading(false);
    }
  }, [authFetch, API_BASE, setApiKeys]);

  useEffect(() => {
    fetchKeys();
  }, [fetchKeys]);

  const handleStore = async (provider: string) => {
    if (!keyInput.trim()) return;
    setSaving(true);
    setFeedback(null);
    try {
      const res = await authFetch(`${API_BASE}/api/settings/keys`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, key: keyInput, label: labelInput || null }),
      });
      if (!res.ok) {
        const err = await res.json();
        setFeedback({ type: 'error', message: err.detail || 'Failed to store key' });
        return;
      }
      const data: KeyStoreResponse = await res.json();
      setFeedback({ type: 'success', message: data.message });
      setKeyInput('');
      setLabelInput('');
      setShowKey(false);
      setAddingProvider(null);
      setHasByok(true);
      setKeySource('personal');
      await fetchKeys();
    } catch {
      setFeedback({ type: 'error', message: 'Network error' });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (provider: string) => {
    setDeleting(provider);
    try {
      await authFetch(`${API_BASE}/api/settings/keys/${provider}`, { method: 'DELETE' });
      await fetchKeys();
      // Re-check BYOK status
      const meRes = await authFetch(`${API_BASE}/api/me`);
      const meData = await meRes.json();
      setHasByok(meData.has_byok || false);
      setKeySource(meData.key_source || 'platform');
    } catch {
      console.error('Failed to delete key');
    } finally {
      setDeleting(null);
    }
  };

  const getKeyForProvider = (provider: string): KeyInfo | undefined =>
    apiKeys.find((k) => k.provider === provider);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress size={32} />
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {/* Key source banner */}
      <Alert
        severity={hasByok ? 'success' : 'info'}
        variant="outlined"
        sx={{ borderRadius: 2 }}
      >
        <Typography variant="body2">
          <strong>Using:</strong> {keySource === 'personal' ? 'Personal Key' : 'Platform Key'}
        </Typography>
        {!hasByok && (
          <Typography variant="caption" color="text.secondary">
            Add your own API key to bypass daily rate limits
          </Typography>
        )}
      </Alert>

      {/* Coming Soon notice */}
      <Alert severity="warning" variant="outlined" sx={{ borderRadius: 2 }}>
        <Typography variant="body2">
          <strong>Coming Soon:</strong> Stored keys are not yet used for LLM calls.
          All sessions currently use the platform key. Adding a key bypasses rate limits.
        </Typography>
      </Alert>

      {feedback && (
        <Alert severity={feedback.type} onClose={() => setFeedback(null)} sx={{ borderRadius: 2 }}>
          {feedback.message}
        </Alert>
      )}

      {/* Provider cards */}
      {supportedProviders.map((provider) => {
        const stored = getKeyForProvider(provider);
        const isAdding = addingProvider === provider;

        return (
          <Card
            key={provider}
            variant="outlined"
            sx={{
              borderRadius: 2,
              bgcolor: darkMode ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.01)',
            }}
          >
            <CardContent sx={{ '&:last-child': { pb: 2 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: stored || isAdding ? 1 : 0 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="subtitle1" fontWeight={600}>
                    {PROVIDER_LABELS[provider] || provider}
                  </Typography>
                  {stored && (
                    <Chip
                      icon={stored.is_valid ? <CheckCircle /> : <Cancel />}
                      label={
                        stored.is_valid
                          ? `Active ····${stored.key_hint || '****'}`
                          : 'Invalid'
                      }
                      size="small"
                      color={stored.is_valid ? 'success' : 'error'}
                      variant="outlined"
                    />
                  )}
                  {!stored && !isAdding && (
                    <Chip label="Not configured" size="small" variant="outlined" />
                  )}
                </Box>
                <Box>
                  {stored && (
                    <IconButton
                      size="small"
                      onClick={() => handleDelete(provider)}
                      disabled={deleting === provider}
                      color="error"
                    >
                      {deleting === provider ? <CircularProgress size={18} /> : <DeleteIcon fontSize="small" />}
                    </IconButton>
                  )}
                  {!stored && !isAdding && (
                    <Button
                      size="small"
                      startIcon={<AddIcon />}
                      onClick={() => { setAddingProvider(provider); setKeyInput(''); setLabelInput(''); setFeedback(null); }}
                    >
                      Add Key
                    </Button>
                  )}
                  {stored && !isAdding && (
                    <Button
                      size="small"
                      onClick={() => { setAddingProvider(provider); setKeyInput(''); setLabelInput(''); setFeedback(null); }}
                    >
                      Replace
                    </Button>
                  )}
                </Box>
              </Box>

              {stored?.label && (
                <Typography variant="caption" color="text.secondary">
                  Label: {stored.label}
                </Typography>
              )}

              {/* Inline add/replace form */}
              {isAdding && (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mt: 1 }}>
                  <TextField
                    fullWidth
                    size="small"
                    type={showKey ? 'text' : 'password'}
                    placeholder={`Enter your ${PROVIDER_LABELS[provider] || provider} API key`}
                    value={keyInput}
                    onChange={(e) => setKeyInput(e.target.value)}
                    InputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton size="small" onClick={() => setShowKey(!showKey)}>
                            {showKey ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                  />
                  <TextField
                    fullWidth
                    size="small"
                    placeholder="Label (optional)"
                    value={labelInput}
                    onChange={(e) => setLabelInput(e.target.value)}
                  />
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="contained"
                      size="small"
                      onClick={() => handleStore(provider)}
                      disabled={!keyInput.trim() || saving}
                      startIcon={saving ? <CircularProgress size={16} /> : undefined}
                    >
                      {saving ? 'Validating...' : 'Validate & Save'}
                    </Button>
                    <Button
                      size="small"
                      onClick={() => { setAddingProvider(null); setFeedback(null); }}
                    >
                      Cancel
                    </Button>
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        );
      })}
    </Box>
  );
}
