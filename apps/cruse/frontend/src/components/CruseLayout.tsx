'use client';

import { Box } from '@mui/material';
import { AnimatePresence, motion } from 'framer-motion';
import { useCruseStore } from '@/store/cruseStore';
import { Header } from '@/components/Header';
import { ChatPanel } from '@/components/chat/ChatPanel';
import { InputBar } from '@/components/InputBar';
import { WidgetCard } from '@/components/widget/WidgetCard';
import { AgentActivityBar } from '@/components/activity/AgentActivityBar';
import { DebugDrawer } from '@/components/debug/DebugDrawer';
import { NetworkDrawer } from '@/components/network/NetworkDrawer';
import { BackgroundEngine } from '@/components/theme/BackgroundEngine';
import { SpotlightTour } from '@/components/tour/SpotlightTour';

export function CruseLayout() {
  const widgetSchema = useCruseStore((s) => s.widgetSchema);
  const darkMode = useCruseStore((s) => s.darkMode);
  const hasWidget = widgetSchema !== null;
  const widgetColor = widgetSchema && !('_html' in widgetSchema) ? (widgetSchema.color || '#3b82f6') : null;

  return (
    <Box
      sx={{
        height: '100vh',
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
          gap: 2,
          px: 2,
          pb: 2,
          overflow: 'hidden',
          position: 'relative',
          zIndex: 1,
        }}
      >
        {/* Widget panel (left) */}
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

      {/* Debug monitor drawer */}
      <DebugDrawer />

      {/* Network visualization drawer */}
      <NetworkDrawer />

      {/* Spotlight walkthrough tour */}
      <SpotlightTour />
    </Box>
  );
}
