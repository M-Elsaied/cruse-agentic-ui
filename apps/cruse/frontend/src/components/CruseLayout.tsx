'use client';

import { useCallback, useEffect } from 'react';
import { Box, Drawer, Fab, useMediaQuery, useTheme } from '@mui/material';
import { Widgets as WidgetsIcon } from '@mui/icons-material';
import { AnimatePresence, motion } from 'framer-motion';
import { useCruseStore } from '@/store/cruseStore';
import { Header } from '@/components/Header';
import { ChatPanel } from '@/components/chat/ChatPanel';
import { InputBar } from '@/components/InputBar';
import { WidgetCard } from '@/components/widget/WidgetCard';
import { AgentActivityBar } from '@/components/activity/AgentActivityBar';
import { AdminDrawer } from '@/components/admin/AdminDrawer';
import { DebugDrawer } from '@/components/debug/DebugDrawer';
import { FeedbackDialog } from '@/components/feedback/FeedbackDialog';
import { HistoryDrawer } from '@/components/history/HistoryDrawer';
import { NetworkDrawer } from '@/components/network/NetworkDrawer';
import { NetworkEditorDrawer } from '@/components/network-editor/NetworkEditorDrawer';
import { SettingsDrawer } from '@/components/settings/SettingsDrawer';
import { BackgroundEngine } from '@/components/theme/BackgroundEngine';
import { SpotlightTour } from '@/components/tour/SpotlightTour';
import { useWebSocket } from '@/hooks/useWebSocket';

function formatFormData(data: Record<string, unknown>): string {
  const entries = Object.entries(data).filter(
    ([, v]) => v !== undefined && v !== null && v !== '',
  );
  if (entries.length === 0) return '<form submitted>';
  const lines = entries.map(
    ([k, v]) => `• ${k.replace(/([a-z])([A-Z])/g, '$1 $2').replace(/[_-]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}: ${v}`,
  );
  return `Form submitted:\n${lines.join('\n')}`;
}

export function CruseLayout() {
  const muiTheme = useTheme();
  const isMobile = useMediaQuery(muiTheme.breakpoints.down('md'));
  const widgetSchema = useCruseStore((s) => s.widgetSchema);
  const darkMode = useCruseStore((s) => s.darkMode);
  const widgetDrawerOpen = useCruseStore((s) => s.widgetDrawerOpen);
  const setWidgetDrawerOpen = useCruseStore((s) => s.setWidgetDrawerOpen);
  const widgetFormData = useCruseStore((s) => s.widgetFormData);
  const setWidgetSubmitted = useCruseStore((s) => s.setWidgetSubmitted);
  const { sendMessage } = useWebSocket();
  const hasWidget = widgetSchema !== null;
  const widgetColor = widgetSchema && !('_html' in widgetSchema) ? (widgetSchema.color || '#3b82f6') : null;

  const handleMobileSubmit = useCallback(() => {
    if (Object.keys(widgetFormData).length > 0) {
      sendMessage(formatFormData(widgetFormData), widgetFormData);
      setWidgetSubmitted(true);
      setWidgetDrawerOpen(false);
    }
  }, [widgetFormData, sendMessage, setWidgetSubmitted, setWidgetDrawerOpen]);

  // Auto-open widget drawer on mobile when a new widget arrives
  useEffect(() => {
    if (isMobile && widgetSchema) {
      setWidgetDrawerOpen(true);
    }
  }, [isMobile, widgetSchema, setWidgetDrawerOpen]);

  return (
    <Box
      sx={{
        height: '100dvh',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        bgcolor: darkMode ? '#0f172a' : '#f8fafc',
      }}
    >
      {/* Dynamic background */}
      <BackgroundEngine />

      {/* Widget color ambient glow */}
      <AnimatePresence>
        {widgetColor && (
          <motion.div
            key={widgetColor}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.8 }}
            style={{
              position: 'absolute',
              inset: 0,
              zIndex: 0,
              background: `radial-gradient(ellipse at 20% 50%, ${widgetColor}${darkMode ? '18' : '10'} 0%, transparent 60%)`,
              pointerEvents: 'none',
            }}
          />
        )}
      </AnimatePresence>

      {/* Header */}
      <Header />

      {/* Agent activity bar */}
      <AgentActivityBar />

      {/* Main content */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          gap: { xs: 0, md: 2 },
          px: { xs: 1, md: 2 },
          pb: { xs: 1, md: 2 },
          overflow: 'hidden',
          position: 'relative',
          zIndex: 1,
        }}
      >
        {/* Widget panel (left) — desktop only, inline */}
        {!isMobile && (
          <div data-tour="widget-area" style={{ alignSelf: 'stretch', display: hasWidget ? 'block' : 'none' }}>
            <AnimatePresence mode="wait">
              {hasWidget && (
                <motion.div
                  key="widget-panel"
                  initial={{ width: 0, opacity: 0 }}
                  animate={{ width: 420, opacity: 1 }}
                  exit={{ width: 0, opacity: 0 }}
                  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                  style={{ flexShrink: 0, overflow: 'hidden' }}
                >
                  <Box
                    className="glass-panel"
                    sx={{
                      height: '100%',
                      overflow: 'auto',
                      p: 0,
                    }}
                  >
                    <WidgetCard />
                  </Box>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* Chat panel (right, fills remaining space) */}
        <Box
          data-tour="chat-panel"
          className="glass-panel"
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            minWidth: 0,
          }}
        >
          <ChatPanel />
          <InputBar />
        </Box>
      </Box>

      {/* Widget drawer — mobile only, bottom sheet */}
      {isMobile && (
        <Drawer
          anchor="bottom"
          open={widgetDrawerOpen && hasWidget}
          onClose={() => setWidgetDrawerOpen(false)}
          PaperProps={{
            sx: {
              maxHeight: '80vh',
              borderTopLeftRadius: 16,
              borderTopRightRadius: 16,
              overflow: 'auto',
            },
          }}
        >
          <Box sx={{ p: 0 }}>
            <WidgetCard onSubmit={handleMobileSubmit} />
          </Box>
        </Drawer>
      )}

      {/* FAB to re-open widget drawer on mobile when dismissed */}
      {isMobile && hasWidget && !widgetDrawerOpen && (
        <Fab
          color="primary"
          size="small"
          onClick={() => setWidgetDrawerOpen(true)}
          sx={{
            position: 'fixed',
            bottom: 80,
            right: 16,
            zIndex: 10,
          }}
        >
          <WidgetsIcon />
        </Fab>
      )}

      {/* Conversation history drawer */}
      <HistoryDrawer />

      {/* Admin console drawer */}
      <AdminDrawer />

      {/* Debug monitor drawer */}
      <DebugDrawer />

      {/* Network visualization drawer */}
      <NetworkDrawer />

      {/* Network editor drawer */}
      <NetworkEditorDrawer />

      {/* Settings drawer */}
      <SettingsDrawer />

      {/* Feedback dialog */}
      <FeedbackDialog />

      {/* Spotlight walkthrough tour */}
      <SpotlightTour />
    </Box>
  );
}
