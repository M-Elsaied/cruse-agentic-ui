'use client';

import { useEffect } from 'react';
import dynamic from 'next/dynamic';
import { Box, CircularProgress } from '@mui/material';
import { useAuth, useOrganization } from '@clerk/nextjs';
import { useCruseStore } from '@/store/cruseStore';
import { useAuthenticatedFetch } from '@/utils/api';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { ConnectionStatus } from '@/components/common/ConnectionStatus';
import { useSessionPersistence } from '@/hooks/useSessionPersistence';
import { LandingPage } from '@/components/landing/LandingPage';

const CruseLayout = dynamic(() => import('@/components/CruseLayout').then((m) => m.CruseLayout), {
  ssr: false,
});

export default function Home() {
  const { isSignedIn, isLoaded } = useAuth();

  if (!isLoaded) {
    return (
      <Box
        sx={{
          height: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: '#0f172a',
        }}
      >
        <CircularProgress sx={{ color: '#3b82f6' }} />
      </Box>
    );
  }

  if (!isSignedIn) {
    return <LandingPage />;
  }

  return <AuthenticatedHome />;
}

function AuthenticatedHome() {
  const setAvailableSystems = useCruseStore((s) => s.setAvailableSystems);
  const setCustomNetworks = useCruseStore((s) => s.setCustomNetworks);
  const setUserRole = useCruseStore((s) => s.setUserRole);
  const setOrgInfo = useCruseStore((s) => s.setOrgInfo);
  const setRateLimit = useCruseStore((s) => s.setRateLimit);
  const setHasByok = useCruseStore((s) => s.setHasByok);
  const setKeySource = useCruseStore((s) => s.setKeySource);
  const { authFetch, API_BASE } = useAuthenticatedFetch();
  const { organization } = useOrganization();
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
        if (systemsData.custom_networks) {
          setCustomNetworks(systemsData.custom_networks);
        }
        const meData = await meRes.json();
        setUserRole((meData.role === 'admin' ? 'admin' : 'user') as 'admin' | 'user');
        setOrgInfo(meData.org_name || null, meData.org_slug || null, meData.is_org_admin || false);
        if (meData.rate_limit) {
          setRateLimit(meData.rate_limit.remaining, meData.rate_limit.limit);
        }
        setHasByok(meData.has_byok || false);
        setKeySource(meData.key_source || 'platform');
      } catch (err) {
        console.error('Failed to fetch init data:', err);
      }
    };
    fetchInit();
  }, [authFetch, API_BASE, setAvailableSystems, setCustomNetworks, setUserRole, setOrgInfo, setRateLimit, setHasByok, setKeySource, organization?.id]);

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
