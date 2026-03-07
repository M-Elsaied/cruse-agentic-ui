'use client';

import { Box, Drawer, IconButton, Tab, Tabs, Typography, useMediaQuery, useTheme } from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { useCruseStore } from '@/store/cruseStore';
import { ApiKeysPanel } from '@/components/settings/ApiKeysPanel';
import { PreferencesPanel } from '@/components/settings/PreferencesPanel';

export function SettingsDrawer() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const open = useCruseStore((s) => s.settingsDrawerOpen);
  const toggleSettingsDrawer = useCruseStore((s) => s.toggleSettingsDrawer);
  const activeTab = useCruseStore((s) => s.settingsActiveTab);
  const setActiveTab = useCruseStore((s) => s.setSettingsActiveTab);
  const darkMode = useCruseStore((s) => s.darkMode);

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={toggleSettingsDrawer}
      PaperProps={{
        sx: {
          width: isMobile ? '100vw' : 480,
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
          <Typography variant="h6" fontWeight={700}>
            Settings
          </Typography>
          <IconButton onClick={toggleSettingsDrawer} size="small">
            <CloseIcon />
          </IconButton>
        </Box>

        {/* Tabs */}
        <Tabs
          value={activeTab}
          onChange={(_, v) => setActiveTab(v)}
          sx={{
            px: 2,
            borderBottom: '1px solid',
            borderColor: darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
          }}
        >
          <Tab label="API Keys" />
          <Tab label="Preferences" />
        </Tabs>

        {/* Content */}
        <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
          {activeTab === 0 && <ApiKeysPanel />}
          {activeTab === 1 && <PreferencesPanel />}
        </Box>
      </Box>
    </Drawer>
  );
}
