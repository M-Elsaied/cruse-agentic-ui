'use client';

import { useEffect } from 'react';
import { useUser } from '@clerk/nextjs';
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
  const { user } = useUser();
  useSessionPersistence();

  useEffect(() => {
    if (user) {
      const role = (user.publicMetadata?.role as string) || 'user';
      setUserRole(role as 'admin' | 'user');
    }
  }, [user, setUserRole]);

  useEffect(() => {
    const fetchSystems = async () => {
      try {
        const res = await authFetch(`${API_BASE}/api/systems`);
        const data = await res.json();
        setAvailableSystems(data.systems || []);
      } catch (err) {
        console.error('Failed to fetch systems:', err);
      }
    };
    fetchSystems();
  }, [authFetch, API_BASE, setAvailableSystems]);

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
