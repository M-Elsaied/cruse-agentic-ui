'use client';

import { useEffect } from 'react';
import { Box } from '@mui/material';
import { useCruseStore } from '@/store/cruseStore';
import { useAuthenticatedFetch } from '@/utils/api';
import { CruseLayout } from '@/components/CruseLayout';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { ConnectionStatus } from '@/components/common/ConnectionStatus';
import { useSessionPersistence } from '@/hooks/useSessionPersistence';

export default function Home() {
  const setAvailableSystems = useCruseStore((s) => s.setAvailableSystems);
  const setUserRole = useCruseStore((s) => s.setUserRole);
  const { authFetch, API_BASE } = useAuthenticatedFetch();
  useSessionPersistence();

  useEffect(() => {
    const fetchInit = async () => {
      try {
        const [systemsRes, meRes] = await Promise.all([
          authFetch(`${API_BASE}/api/systems`),
          authFetch(`${API_BASE}/api/me`),
        ]);
        const systemsData = await systemsRes.json();
        setAvailableSystems(systemsData.systems || []);
        const meData = await meRes.json();
        setUserRole((meData.role === 'admin' ? 'admin' : 'user') as 'admin' | 'user');
      } catch (err) {
        console.error('Failed to fetch init data:', err);
      }
    };
    fetchInit();
  }, [authFetch, API_BASE, setAvailableSystems, setUserRole]);

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
