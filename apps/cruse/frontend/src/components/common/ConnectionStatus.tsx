'use client';

import { Snackbar, Alert } from '@mui/material';
import { useCruseStore } from '@/store/cruseStore';

export function ConnectionStatus() {
  const isConnected = useCruseStore((s) => s.isConnected);
  const connectionError = useCruseStore((s) => s.connectionError);
  const sessionId = useCruseStore((s) => s.sessionId);
  const setConnectionError = useCruseStore((s) => s.setConnectionError);

  // Only show disconnection warning when we have a session but lost connection
  const showDisconnected = sessionId && !isConnected && !connectionError;

  return (
    <>
      {/* Connection error */}
      <Snackbar
        open={!!connectionError}
        autoHideDuration={6000}
        onClose={() => setConnectionError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          severity="error"
          variant="filled"
          onClose={() => setConnectionError(null)}
          sx={{ width: '100%' }}
        >
          {connectionError}
        </Alert>
      </Snackbar>

      {/* Disconnected warning */}
      <Snackbar
        open={!!showDisconnected}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity="warning" variant="filled" sx={{ width: '100%' }}>
          Connection lost. Attempting to reconnect...
        </Alert>
      </Snackbar>
    </>
  );
}
