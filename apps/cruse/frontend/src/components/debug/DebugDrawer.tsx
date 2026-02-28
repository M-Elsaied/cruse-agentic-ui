'use client';

import { Box, Drawer, IconButton, Tab, Tabs, Typography, Badge, Tooltip } from '@mui/material';
import { Close, DeleteOutline } from '@mui/icons-material';
import { AnimatePresence, motion } from 'framer-motion';
import { useCruseStore } from '@/store/cruseStore';
import { AgentTracePanel } from '@/components/debug/AgentTracePanel';
import { ServerLogPanel } from '@/components/debug/ServerLogPanel';

const DRAWER_WIDTH = 480;

export function DebugDrawer() {
  const open = useCruseStore((s) => s.debugDrawerOpen);
  const toggleDrawer = useCruseStore((s) => s.toggleDebugDrawer);
  const activeTab = useCruseStore((s) => s.debugActiveTab);
  const setActiveTab = useCruseStore((s) => s.setDebugActiveTab);
  const traceCount = useCruseStore((s) => s.debugTraceEntries.length);
  const logCount = useCruseStore((s) => s.debugLogEntries.length);
  const clearEntries = useCruseStore((s) => s.clearDebugEntries);
  const darkMode = useCruseStore((s) => s.darkMode);

  return (
    <Drawer
      anchor="right"
      variant="temporary"
      open={open}
      onClose={toggleDrawer}
      ModalProps={{ keepMounted: true }}
      PaperProps={{
        sx: {
          width: DRAWER_WIDTH,
          maxWidth: '90vw',
          bgcolor: darkMode ? 'rgba(15, 23, 42, 0.92)' : 'rgba(248, 250, 252, 0.92)',
          backdropFilter: 'blur(20px)',
          borderLeft: '1px solid',
          borderColor: darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
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
          Debug Monitor
        </Typography>
        <Tooltip title="Clear all entries">
          <IconButton size="small" onClick={clearEntries}>
            <DeleteOutline fontSize="small" />
          </IconButton>
        </Tooltip>
        <IconButton size="small" onClick={toggleDrawer}>
          <Close fontSize="small" />
        </IconButton>
      </Box>

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onChange={(_, v) => setActiveTab(v)}
        variant="fullWidth"
        sx={{
          minHeight: 40,
          borderBottom: '1px solid',
          borderColor: darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)',
          '& .MuiTab-root': { minHeight: 40, textTransform: 'none', fontSize: '0.8rem' },
        }}
      >
        <Tab
          label={
            <Badge badgeContent={traceCount} color="primary" max={999} sx={{ '& .MuiBadge-badge': { fontSize: '0.6rem', height: 16, minWidth: 16 } }}>
              <span style={{ paddingRight: traceCount > 0 ? 12 : 0 }}>Agent Trace</span>
            </Badge>
          }
        />
        <Tab
          label={
            <Badge badgeContent={logCount} color="info" max={999} sx={{ '& .MuiBadge-badge': { fontSize: '0.6rem', height: 16, minWidth: 16 } }}>
              <span style={{ paddingRight: logCount > 0 ? 12 : 0 }}>Server Logs</span>
            </Badge>
          }
        />
      </Tabs>

      {/* Tab content */}
      <Box sx={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <AnimatePresence mode="wait">
          {activeTab === 0 && (
            <motion.div
              key="trace"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              transition={{ duration: 0.15 }}
              style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}
            >
              <AgentTracePanel />
            </motion.div>
          )}
          {activeTab === 1 && (
            <motion.div
              key="logs"
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.15 }}
              style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}
            >
              <ServerLogPanel />
            </motion.div>
          )}
        </AnimatePresence>
      </Box>
    </Drawer>
  );
}
