'use client';

import { useCallback, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Drawer,
  IconButton,
  Tab,
  Tabs,
  TextField,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Close as CloseIcon,
  Save as SaveIcon,
} from '@mui/icons-material';
import { useCruseStore } from '@/store/cruseStore';
import { useAuthenticatedFetch } from '@/utils/api';
import { NetworkListPanel } from '@/components/network-editor/NetworkListPanel';
import { HoconEditor } from '@/components/network-editor/HoconEditor';

export function NetworkEditorDrawer() {
  const muiTheme = useTheme();
  const isMobile = useMediaQuery(muiTheme.breakpoints.down('md'));
  const open = useCruseStore((s) => s.networkEditorOpen);
  const toggleNetworkEditor = useCruseStore((s) => s.toggleNetworkEditor);
  const darkMode = useCruseStore((s) => s.darkMode);
  const editingNetwork = useCruseStore((s) => s.editingNetwork);
  const setEditingNetwork = useCruseStore((s) => s.setEditingNetwork);
  const { authFetch, API_BASE } = useAuthenticatedFetch();

  const [activeTab, setActiveTab] = useState(0);
  const [editContent, setEditContent] = useState('');
  const [editName, setEditName] = useState('');
  const [saving, setSaving] = useState(false);
  const [validating, setValidating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // When editingNetwork changes, sync local state
  const handleStartEdit = useCallback(() => {
    if (editingNetwork) {
      setEditContent(editingNetwork.hocon_content);
      setEditName(editingNetwork.name);
      setActiveTab(1);
      setError(null);
      setSuccess(null);
    }
  }, [editingNetwork]);

  // Called when setEditingNetwork is triggered from NetworkListPanel
  // We use useEffect-like behavior via the store subscription
  const prevEditingRef = useCruseStore((s) => s.editingNetwork);
  if (prevEditingRef && activeTab === 0) {
    handleStartEdit();
  }

  const handleBack = () => {
    setEditingNetwork(null);
    setActiveTab(0);
    setError(null);
    setSuccess(null);
  };

  const handleValidate = async () => {
    setValidating(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await authFetch(`${API_BASE}/api/networks/validate`, {
        method: 'POST',
        body: JSON.stringify({ hocon_content: editContent }),
      });
      const data = await res.json();
      if (data.valid) {
        setSuccess('HOCON is valid');
      } else {
        setError(data.errors?.[0] || 'Invalid HOCON');
      }
    } catch {
      setError('Validation request failed');
    } finally {
      setValidating(false);
    }
  };

  const handleSave = async () => {
    if (!editingNetwork) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await authFetch(`${API_BASE}/api/networks/${editingNetwork.id}`, {
        method: 'PUT',
        body: JSON.stringify({
          hocon_content: editContent,
          name: editName !== editingNetwork.name ? editName : null,
        }),
      });
      if (!res.ok) {
        const data = await res.json();
        setError(data.detail || 'Failed to save');
        return;
      }
      const updated = await res.json();
      setEditingNetwork(updated);
      setSuccess('Network saved successfully');
    } catch {
      setError('Failed to save network');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={toggleNetworkEditor}
      PaperProps={{
        sx: {
          width: isMobile ? '100vw' : 640,
          bgcolor: darkMode ? '#0f172a' : '#f8fafc',
          backgroundImage: 'none',
        },
      }}
    >
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* Header */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            px: 2,
            py: 1.5,
            borderBottom: '1px solid',
            borderColor: darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {activeTab === 1 && (
              <IconButton onClick={handleBack} size="small">
                <ArrowBackIcon />
              </IconButton>
            )}
            <Typography variant="h6" fontWeight={700}>
              {activeTab === 0 ? 'Custom Networks' : editingNetwork?.name || 'Editor'}
            </Typography>
          </Box>
          <IconButton onClick={toggleNetworkEditor} size="small">
            <CloseIcon />
          </IconButton>
        </Box>

        {/* Tabs */}
        <Tabs
          value={activeTab}
          onChange={(_, v) => {
            if (v === 0) handleBack();
            else setActiveTab(v);
          }}
          sx={{
            px: 2,
            borderBottom: '1px solid',
            borderColor: darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
          }}
        >
          <Tab label="Networks" />
          <Tab label="Editor" disabled={!editingNetwork} />
        </Tabs>

        {/* Content */}
        <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
          {activeTab === 0 && <NetworkListPanel />}
          {activeTab === 1 && editingNetwork && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {error && <Alert severity="error" onClose={() => setError(null)}>{error}</Alert>}
              {success && <Alert severity="success" onClose={() => setSuccess(null)}>{success}</Alert>}

              <TextField
                label="Name"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                size="small"
                fullWidth
              />

              <Typography variant="caption" color="text.secondary">
                Slug: {editingNetwork.slug} (immutable)
              </Typography>

              <HoconEditor
                value={editContent}
                onChange={setEditContent}
                height="calc(100vh - 380px)"
              />

              <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                <Button
                  variant="outlined"
                  onClick={handleValidate}
                  disabled={validating || !editContent.trim()}
                >
                  {validating ? 'Validating...' : 'Validate'}
                </Button>
                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={handleSave}
                  disabled={saving || !editContent.trim()}
                >
                  {saving ? 'Saving...' : 'Save'}
                </Button>
              </Box>
            </Box>
          )}
        </Box>
      </Box>
    </Drawer>
  );
}
