'use client';

import { useCallback, useEffect, useState } from 'react';
import { Box, CircularProgress, Drawer, IconButton, Tooltip, Typography } from '@mui/material';
import { Close, Refresh } from '@mui/icons-material';
import { useCruseStore } from '@/store/cruseStore';
import { NetworkGraph } from '@/components/network/NetworkGraph';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';
export function NetworkDrawer() {
  const open = useCruseStore((s) => s.networkDrawerOpen);
  const toggleDrawer = useCruseStore((s) => s.toggleNetworkDrawer);
  const agentNetwork = useCruseStore((s) => s.agentNetwork);
  const connectivityData = useCruseStore((s) => s.connectivityData);
  const connectivityLoading = useCruseStore((s) => s.connectivityLoading);
  const setConnectivityData = useCruseStore((s) => s.setConnectivityData);
  const setConnectivityLoading = useCruseStore((s) => s.setConnectivityLoading);
  const darkMode = useCruseStore((s) => s.darkMode);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchConnectivity = useCallback(async (network: string) => {
    setConnectivityLoading(true);
    setConnectivityData(null);
    setErrorMsg(null);
    try {
      const url = `${API_BASE}/api/connectivity/${network}`;
      const res = await fetch(url);
      if (!res.ok) {
        const detail = await res.text().catch(() => '');
        throw new Error(`HTTP ${res.status}: ${detail}`);
      }
      const data = await res.json();
      setConnectivityData(data);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      console.error('Failed to fetch connectivity:', msg);
      setErrorMsg(msg);
    } finally {
      setConnectivityLoading(false);
    }
  }, [setConnectivityData, setConnectivityLoading]);

  // Fetch when drawer opens or network changes
  useEffect(() => {
    if (open && agentNetwork) {
      fetchConnectivity(agentNetwork);
    }
  }, [open, agentNetwork, fetchConnectivity]);

  return (
    <Drawer
      anchor="right"
      variant="temporary"
      open={open}
      onClose={toggleDrawer}
      ModalProps={{ keepMounted: true }}
      PaperProps={{
        sx: {
          width: '100vw',
          height: '100vh',
          bgcolor: darkMode ? 'rgba(15, 23, 42, 0.95)' : 'rgba(248, 250, 252, 0.95)',
          backdropFilter: 'blur(20px)',
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          px: 2,
          py: 1.5,
          borderBottom: '1px solid',
          borderColor: darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
        }}
      >
        <Typography variant="subtitle1" sx={{ fontWeight: 700, flex: 1 }}>
          Agent Network
        </Typography>
        <Tooltip title="Refresh">
          <span>
            <IconButton
              size="small"
              onClick={() => agentNetwork && fetchConnectivity(agentNetwork)}
              disabled={connectivityLoading || !agentNetwork}
            >
              <Refresh fontSize="small" />
            </IconButton>
          </span>
        </Tooltip>
        <IconButton size="small" onClick={toggleDrawer}>
          <Close fontSize="small" />
        </IconButton>
      </Box>

      {/* Body */}
      <Box sx={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {connectivityLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flex: 1 }}>
            <CircularProgress size={32} />
          </Box>
        )}

        {!connectivityLoading && !connectivityData && (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              {!agentNetwork
                ? 'Select an agent network to view its topology.'
                : errorMsg
                  ? `Failed to load network data: ${errorMsg}`
                  : 'Failed to load network data.'}
            </Typography>
          </Box>
        )}

        {!connectivityLoading && connectivityData && (
          <NetworkGraph data={connectivityData} />
        )}
      </Box>
    </Drawer>
  );
}
