'use client';

import { Box, Drawer, IconButton, Tab, Tabs, Typography } from '@mui/material';
import { Close } from '@mui/icons-material';
import { AnimatePresence, motion } from 'framer-motion';
import { useState } from 'react';
import { useCruseStore } from '@/store/cruseStore';
import { AdminConversationsPanel } from '@/components/admin/AdminConversationsPanel';
import { AdminReportsPanel } from '@/components/admin/AdminReportsPanel';
import { AdminSessionsPanel } from '@/components/admin/AdminSessionsPanel';
import { AdminStatsPanel } from '@/components/admin/AdminStatsPanel';

const DRAWER_WIDTH = 560;

export function AdminDrawer() {
  const open = useCruseStore((s) => s.adminDrawerOpen);
  const toggleDrawer = useCruseStore((s) => s.toggleAdminDrawer);
  const darkMode = useCruseStore((s) => s.darkMode);
  const [activeTab, setActiveTab] = useState(0);

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
          Admin Console
        </Typography>
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
        <Tab label="Sessions" />
        <Tab label="Conversations" />
        <Tab label="Stats" />
        <Tab label="Reports" />
      </Tabs>

      {/* Tab content */}
      <Box sx={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <AnimatePresence mode="wait">
          {activeTab === 0 && (
            <motion.div
              key="sessions"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              transition={{ duration: 0.15 }}
              style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}
            >
              <AdminSessionsPanel />
            </motion.div>
          )}
          {activeTab === 1 && (
            <motion.div
              key="conversations"
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.15 }}
              style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}
            >
              <AdminConversationsPanel />
            </motion.div>
          )}
          {activeTab === 2 && (
            <motion.div
              key="stats"
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.15 }}
              style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}
            >
              <AdminStatsPanel />
            </motion.div>
          )}
          {activeTab === 3 && (
            <motion.div
              key="reports"
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.15 }}
              style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}
            >
              <AdminReportsPanel />
            </motion.div>
          )}
        </AnimatePresence>
      </Box>
    </Drawer>
  );
}
