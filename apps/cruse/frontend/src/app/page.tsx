'use client';

import { useEffect } from 'react';
import { Box } from '@mui/material';
import { useCruseStore } from '@/store/cruseStore';
import { CruseLayout } from '@/components/CruseLayout';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { ConnectionStatus } from '@/components/common/ConnectionStatus';
import { useSessionPersistence } from '@/hooks/useSessionPersistence';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

export default function Home() {
  const setAvailableSystems = useCruseStore((s) => s.setAvailableSystems);
  useSessionPersistence();

  useEffect(() => {
    const fetchSystems = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/systems`);
        const data = await res.json();
        setAvailableSystems(data.systems || []);
      } catch (err) {
        console.error('Failed to fetch systems:', err);
      }
    };
    fetchSystems();
  }, [setAvailableSystems]);

  return (
    <ErrorBoundary>
      <Box
        sx={{
          height: '100vh',
          width: '100vw',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        <CruseLayout />
        <ConnectionStatus />
      </Box>
    </ErrorBoundary>
  );
}
