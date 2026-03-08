'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Lock as LockIcon,
  LockOpen as LockOpenIcon,
} from '@mui/icons-material';
import { useCruseStore } from '@/store/cruseStore';
import { useAuthenticatedFetch } from '@/utils/api';
import type { NetworkDetail, NetworkInfo } from '@/types/network-editor';

export function NetworkListPanel() {
  const darkMode = useCruseStore((s) => s.darkMode);
  const customNetworks = useCruseStore((s) => s.customNetworks);
  const setCustomNetworks = useCruseStore((s) => s.setCustomNetworks);
  const setEditingNetwork = useCruseStore((s) => s.setEditingNetwork);
  const networkEditorLoading = useCruseStore((s) => s.networkEditorLoading);
  const setNetworkEditorLoading = useCruseStore((s) => s.setNetworkEditorLoading);
  const { authFetch, API_BASE } = useAuthenticatedFetch();

  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newSlug, setNewSlug] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [error, setError] = useState<string | null>(null);

  const loadNetworks = useCallback(async () => {
    setNetworkEditorLoading(true);
    try {
      const res = await authFetch(`${API_BASE}/api/networks`);
      if (res.ok) {
        const data = await res.json();
        setCustomNetworks(data);
      }
    } catch (err) {
      console.error('Failed to load networks:', err);
    } finally {
      setNetworkEditorLoading(false);
    }
  }, [authFetch, API_BASE, setCustomNetworks, setNetworkEditorLoading]);

  useEffect(() => {
    loadNetworks();
  }, [loadNetworks]);

  const handleCreate = async () => {
    setError(null);
    try {
      const res = await authFetch(`${API_BASE}/api/networks`, {
        method: 'POST',
        body: JSON.stringify({
          name: newName,
          slug: newSlug,
          hocon_content: '{\n  llm_config {\n    class_name = ChatOpenAI\n    model_name = gpt-4o-mini\n  }\n  tools = []\n}\n',
          description: newDescription || null,
        }),
      });
      if (!res.ok) {
        const data = await res.json();
        setError(data.detail || 'Failed to create network');
        return;
      }
      const detail: NetworkDetail = await res.json();
      setCreateOpen(false);
      setNewName('');
      setNewSlug('');
      setNewDescription('');
      setEditingNetwork(detail);
      await loadNetworks();
    } catch (err) {
      setError('Failed to create network');
    }
  };

  const handleEdit = async (net: NetworkInfo) => {
    try {
      const res = await authFetch(`${API_BASE}/api/networks/${net.id}`);
      if (res.ok) {
        const detail: NetworkDetail = await res.json();
        setEditingNetwork(detail);
      }
    } catch (err) {
      console.error('Failed to load network detail:', err);
    }
  };

  const handleToggleShare = async (net: NetworkInfo) => {
    try {
      await authFetch(`${API_BASE}/api/networks/${net.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ is_shared: !net.is_shared }),
      });
      await loadNetworks();
    } catch (err) {
      console.error('Failed to toggle sharing:', err);
    }
  };

  const handleDelete = async (net: NetworkInfo) => {
    if (!confirm(`Delete "${net.name}"? This cannot be undone.`)) return;
    try {
      await authFetch(`${API_BASE}/api/networks/${net.id}`, { method: 'DELETE' });
      await loadNetworks();
    } catch (err) {
      console.error('Failed to delete network:', err);
    }
  };

  const autoSlug = (name: string) => {
    return name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
  };

  if (networkEditorLoading && customNetworks.my_networks.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress size={32} />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="subtitle1" fontWeight={600}>
          My Networks ({customNetworks.my_networks.length})
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          size="small"
          onClick={() => setCreateOpen(true)}
        >
          Create
        </Button>
      </Box>

      {/* My Networks */}
      {customNetworks.my_networks.length === 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          No custom networks yet. Click Create to get started.
        </Typography>
      )}
      {customNetworks.my_networks.map((net) => (
        <NetworkCard
          key={net.id}
          network={net}
          isOwner
          darkMode={darkMode}
          onEdit={() => handleEdit(net)}
          onToggleShare={() => handleToggleShare(net)}
          onDelete={() => handleDelete(net)}
        />
      ))}

      {/* Shared Networks */}
      {customNetworks.shared_networks.length > 0 && (
        <>
          <Typography variant="subtitle1" fontWeight={600} sx={{ mt: 3, mb: 1 }}>
            Shared With Me ({customNetworks.shared_networks.length})
          </Typography>
          {customNetworks.shared_networks.map((net) => (
            <NetworkCard
              key={net.id}
              network={net}
              isOwner={false}
              darkMode={darkMode}
              onEdit={() => handleEdit(net)}
            />
          ))}
        </>
      )}

      {/* Create Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Network</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '8px !important' }}>
          {error && <Alert severity="error" onClose={() => setError(null)}>{error}</Alert>}
          <TextField
            label="Name"
            value={newName}
            onChange={(e) => {
              setNewName(e.target.value);
              if (!newSlug || newSlug === autoSlug(newName)) {
                setNewSlug(autoSlug(e.target.value));
              }
            }}
            fullWidth
            size="small"
          />
          <TextField
            label="Slug (URL-safe identifier)"
            value={newSlug}
            onChange={(e) => setNewSlug(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ''))}
            fullWidth
            size="small"
            helperText="Lowercase letters, digits, and underscores only"
          />
          <TextField
            label="Description (optional)"
            value={newDescription}
            onChange={(e) => setNewDescription(e.target.value)}
            fullWidth
            size="small"
            multiline
            rows={2}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button onClick={handleCreate} variant="contained" disabled={!newName || !newSlug}>
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

function NetworkCard({
  network,
  isOwner,
  darkMode,
  onEdit,
  onToggleShare,
  onDelete,
}: {
  network: NetworkInfo;
  isOwner: boolean;
  darkMode: boolean;
  onEdit: () => void;
  onToggleShare?: () => void;
  onDelete?: () => void;
}) {
  return (
    <Card
      sx={{
        mb: 1.5,
        bgcolor: darkMode ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
        border: '1px solid',
        borderColor: darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
      }}
    >
      <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <Typography variant="subtitle2" fontWeight={600} noWrap>
                {network.name}
              </Typography>
              <Chip
                label={network.is_shared ? 'Shared' : 'Private'}
                icon={network.is_shared ? <LockOpenIcon /> : <LockIcon />}
                size="small"
                variant="outlined"
                sx={{ height: 22, '& .MuiChip-icon': { fontSize: 14 } }}
              />
            </Box>
            {network.description && (
              <Typography variant="caption" color="text.secondary" noWrap>
                {network.description}
              </Typography>
            )}
          </Box>
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <Tooltip title="Edit">
              <IconButton size="small" onClick={onEdit}>
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            {isOwner && onToggleShare && (
              <Tooltip title={network.is_shared ? 'Make private' : 'Share with org'}>
                <IconButton size="small" onClick={onToggleShare}>
                  {network.is_shared ? <LockIcon fontSize="small" /> : <LockOpenIcon fontSize="small" />}
                </IconButton>
              </Tooltip>
            )}
            {isOwner && onDelete && (
              <Tooltip title="Delete">
                <IconButton size="small" onClick={onDelete} color="error">
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}
