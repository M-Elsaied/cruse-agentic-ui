'use client';

import { useCallback, useState } from 'react';
import {
  AppBar,
  Badge,
  Toolbar,
  Tooltip,
  Typography,
  Select,
  MenuItem,
  ListSubheader,
  IconButton,
  Button,
  Box,
  Chip,
  Menu,
  ListItemIcon,
  ListItemText,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  AccountTree,
  AdminPanelSettings,
  BugReport,
  DarkMode,
  LightMode,
  Settings as SettingsIcon,
  Add as AddIcon,
  Code as CodeIcon,
  History as HistoryIcon,
  Hub as HubIcon,
  Menu as MenuIcon,
} from '@mui/icons-material';
import { OrganizationSwitcher, UserButton } from '@clerk/nextjs';
import type { SelectChangeEvent } from '@mui/material';
import { useCruseStore } from '@/store/cruseStore';
import { useAuthenticatedFetch } from '@/utils/api';

export function Header() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileMenuAnchor, setMobileMenuAnchor] = useState<null | HTMLElement>(null);
  const availableSystems = useCruseStore((s) => s.availableSystems);
  const agentNetwork = useCruseStore((s) => s.agentNetwork);
  const sessionId = useCruseStore((s) => s.sessionId);
  const isConnected = useCruseStore((s) => s.isConnected);
  const isStreaming = useCruseStore((s) => s.isStreaming);
  const darkMode = useCruseStore((s) => s.darkMode);

  const setAgentNetwork = useCruseStore((s) => s.setAgentNetwork);
  const setSessionId = useCruseStore((s) => s.setSessionId);
  const clearMessages = useCruseStore((s) => s.clearMessages);
  const setWidgetSchema = useCruseStore((s) => s.setWidgetSchema);
  const setTheme = useCruseStore((s) => s.setTheme);
  const setSampleQueries = useCruseStore((s) => s.setSampleQueries);
  const toggleDarkMode = useCruseStore((s) => s.toggleDarkMode);
  const debugDrawerOpen = useCruseStore((s) => s.debugDrawerOpen);
  const debugUnreadCount = useCruseStore((s) => s.debugUnreadCount);
  const toggleDebugDrawer = useCruseStore((s) => s.toggleDebugDrawer);
  const userRole = useCruseStore((s) => s.userRole);
  const adminDrawerOpen = useCruseStore((s) => s.adminDrawerOpen);
  const toggleAdminDrawer = useCruseStore((s) => s.toggleAdminDrawer);
  const networkDrawerOpen = useCruseStore((s) => s.networkDrawerOpen);
  const toggleNetworkDrawer = useCruseStore((s) => s.toggleNetworkDrawer);
  const historyDrawerOpen = useCruseStore((s) => s.historyDrawerOpen);
  const toggleHistoryDrawer = useCruseStore((s) => s.toggleHistoryDrawer);
  const settingsDrawerOpen = useCruseStore((s) => s.settingsDrawerOpen);
  const toggleSettingsDrawer = useCruseStore((s) => s.toggleSettingsDrawer);
  const networkEditorOpen = useCruseStore((s) => s.networkEditorOpen);
  const toggleNetworkEditor = useCruseStore((s) => s.toggleNetworkEditor);
  const customNetworks = useCruseStore((s) => s.customNetworks);
  const setViewingConversation = useCruseStore((s) => s.setViewingConversation);
  const { authFetch, API_BASE } = useAuthenticatedFetch();

  const createSession = useCallback(
    async (network: string) => {
      // Destroy old session if exists
      if (sessionId) {
        try {
          await authFetch(`${API_BASE}/api/session/${sessionId}`, { method: 'DELETE' });
        } catch {
          // Ignore cleanup errors
        }
      }

      try {
        const res = await authFetch(`${API_BASE}/api/session`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ agent_network: network }),
        });
        const data = await res.json();
        setSessionId(data.session_id);
        setAgentNetwork(network);
        clearMessages();
        setWidgetSchema(null);
        if (data.theme) {
          setTheme(data.theme);
        }
        setSampleQueries(data.sample_queries || []);
      } catch (err) {
        console.error('Failed to create session:', err);
      }
    },
    [sessionId, authFetch, API_BASE, setSessionId, setAgentNetwork, clearMessages, setWidgetSchema, setTheme, setSampleQueries]
  );

  const handleSystemChange = (event: SelectChangeEvent<string>) => {
    const network = event.target.value;
    if (network) {
      createSession(network);
    }
  };

  const handleNewChat = () => {
    if (agentNetwork) {
      setViewingConversation(null);
      createSession(agentNetwork);
    }
  };

  const formatSystemName = (name: string) => {
    // "basic/hello_world" -> "Hello World"
    // "industry/airline_policy" -> "Airline Policy"
    const clean = name.replace(/\.hocon$/, '');
    const base = clean.split('/').pop() || clean;
    return base.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  };

  const getSystemCategory = (name: string): string => {
    const clean = name.replace(/\.hocon$/, '');
    const parts = clean.split('/');
    if (parts.length > 1) return parts[0];
    return '';
  };

  // Group systems by category for the dropdown
  const groupedSystems = availableSystems.reduce<Record<string, string[]>>((acc, sys) => {
    const cat = getSystemCategory(sys) || 'other';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(sys);
    return acc;
  }, {});

  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        background: 'transparent',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid',
        borderColor: darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
        zIndex: 2,
      }}
    >
      <Toolbar sx={{ gap: { xs: 1, md: 2 }, minHeight: { xs: 56, md: 64 } }}>
        {/* Logo */}
        <HubIcon sx={{ color: 'primary.main', fontSize: 28 }} />
        <Typography
          variant="h6"
          sx={{
            fontWeight: 700,
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            mr: { xs: 0, md: 2 },
          }}
        >
          CRUSE
        </Typography>

        {/* Agent network selector */}
        <Select
          data-tour="network-selector"
          value={agentNetwork || ''}
          onChange={handleSystemChange}
          displayEmpty
          size="small"
          disabled={isStreaming}
          sx={{
            minWidth: { xs: 140, md: 240 },
            '& .MuiSelect-select': {
              py: 0.75,
            },
          }}
        >
          <MenuItem value="" disabled>
            Select Agent Network
          </MenuItem>
          {customNetworks.my_networks.length > 0 && [
            <ListSubheader key="header-my" sx={{ fontWeight: 700 }}>
              My Networks
            </ListSubheader>,
            ...customNetworks.my_networks.map((n) => (
              <MenuItem key={`my-${n.network_path}`} value={n.network_path} sx={{ pl: 4 }}>
                {n.name}
              </MenuItem>
            )),
          ]}
          {customNetworks.shared_networks.length > 0 && [
            <ListSubheader key="header-shared" sx={{ fontWeight: 700 }}>
              Shared With Me
            </ListSubheader>,
            ...customNetworks.shared_networks.map((n) => (
              <MenuItem key={`shared-${n.network_path}`} value={n.network_path} sx={{ pl: 4 }}>
                {n.name}
              </MenuItem>
            )),
          ]}
          {Object.entries(groupedSystems).map(([category, systems]) => [
            <ListSubheader key={`header-${category}`} sx={{ textTransform: 'capitalize', fontWeight: 700 }}>
              {category}
            </ListSubheader>,
            ...systems.map((sys) => (
              <MenuItem key={sys} value={sys} sx={{ pl: 4 }}>
                {formatSystemName(sys)}
              </MenuItem>
            )),
          ])}
        </Select>

        {/* Connection status chip — hidden on xs */}
        <Chip
          size="small"
          label={isConnected ? 'Connected' : 'Disconnected'}
          color={isConnected ? 'success' : 'default'}
          variant="outlined"
          sx={{ ml: 1, display: { xs: 'none', sm: 'inline-flex' } }}
        />

        <Box sx={{ flex: 1 }} />

        {/* Desktop action buttons — hidden on mobile */}
        <Box sx={{ display: { xs: 'none', md: 'flex' }, alignItems: 'center', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={handleNewChat}
            disabled={!agentNetwork || isStreaming}
            size="small"
          >
            New Chat
          </Button>

          <Tooltip title={historyDrawerOpen ? 'Close history' : 'Conversation history'}>
            <IconButton onClick={toggleHistoryDrawer} size="small">
              <HistoryIcon sx={{ color: historyDrawerOpen ? '#3b82f6' : undefined }} />
            </IconButton>
          </Tooltip>

          <Tooltip title={networkEditorOpen ? 'Close network editor' : 'Custom networks'}>
            <IconButton onClick={toggleNetworkEditor} size="small">
              <CodeIcon sx={{ color: networkEditorOpen ? '#3b82f6' : undefined }} />
            </IconButton>
          </Tooltip>

          <Tooltip title={settingsDrawerOpen ? 'Close settings' : 'Settings & API Keys'}>
            <IconButton onClick={toggleSettingsDrawer} size="small">
              <SettingsIcon sx={{ color: settingsDrawerOpen ? '#3b82f6' : undefined }} />
            </IconButton>
          </Tooltip>

          <Tooltip title={networkDrawerOpen ? 'Close network view' : 'View agent network'}>
            <span>
              <IconButton onClick={toggleNetworkDrawer} size="small" disabled={!agentNetwork}>
                <AccountTree sx={{ color: networkDrawerOpen ? '#3b82f6' : undefined }} />
              </IconButton>
            </span>
          </Tooltip>

          <Tooltip title={debugDrawerOpen ? 'Close debug monitor' : 'Open debug monitor'}>
            <IconButton data-tour="debug-toggle" onClick={toggleDebugDrawer} size="small">
              <Badge badgeContent={debugUnreadCount} color="error" max={99}>
                <BugReport sx={{ color: debugDrawerOpen ? '#3b82f6' : undefined }} />
              </Badge>
            </IconButton>
          </Tooltip>

          {userRole === 'admin' && (
            <Tooltip title={adminDrawerOpen ? 'Close admin console' : 'Admin console'}>
              <IconButton onClick={toggleAdminDrawer} size="small">
                <AdminPanelSettings sx={{ color: adminDrawerOpen ? '#3b82f6' : undefined }} />
              </IconButton>
            </Tooltip>
          )}

          <IconButton data-tour="theme-toggle" onClick={toggleDarkMode} size="small">
            {darkMode ? (
              <LightMode sx={{ color: '#fbbf24' }} />
            ) : (
              <DarkMode sx={{ color: '#64748b' }} />
            )}
          </IconButton>

          <OrganizationSwitcher
            hidePersonal={false}
            appearance={{
              elements: { rootBox: { display: 'flex', alignItems: 'center' } },
            }}
          />

          <UserButton
            appearance={{
              elements: { avatarBox: { width: 32, height: 32 } },
            }}
          />
        </Box>

        {/* Mobile: dark/light toggle + hamburger menu */}
        <Box sx={{ display: { xs: 'flex', md: 'none' }, alignItems: 'center', gap: 0.5 }}>
          <IconButton data-tour="theme-toggle" onClick={toggleDarkMode} size="small">
            {darkMode ? (
              <LightMode sx={{ color: '#fbbf24' }} />
            ) : (
              <DarkMode sx={{ color: '#64748b' }} />
            )}
          </IconButton>

          <IconButton onClick={(e) => setMobileMenuAnchor(e.currentTarget)} size="small">
            <Badge badgeContent={debugUnreadCount} color="error" max={99} variant="dot">
              <MenuIcon />
            </Badge>
          </IconButton>
        </Box>

        {/* Mobile menu */}
        {isMobile && (
          <Menu
            anchorEl={mobileMenuAnchor}
            open={Boolean(mobileMenuAnchor)}
            onClose={() => setMobileMenuAnchor(null)}
            slotProps={{ paper: { sx: { minWidth: 200 } } }}
          >
            <MenuItem
              onClick={() => { handleNewChat(); setMobileMenuAnchor(null); }}
              disabled={!agentNetwork || isStreaming}
            >
              <ListItemIcon><AddIcon fontSize="small" /></ListItemIcon>
              <ListItemText>New Chat</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => { toggleHistoryDrawer(); setMobileMenuAnchor(null); }}>
              <ListItemIcon><HistoryIcon fontSize="small" /></ListItemIcon>
              <ListItemText>History</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => { toggleNetworkEditor(); setMobileMenuAnchor(null); }}>
              <ListItemIcon><CodeIcon fontSize="small" /></ListItemIcon>
              <ListItemText>Custom Networks</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => { toggleSettingsDrawer(); setMobileMenuAnchor(null); }}>
              <ListItemIcon><SettingsIcon fontSize="small" /></ListItemIcon>
              <ListItemText>Settings</ListItemText>
            </MenuItem>
            <MenuItem
              onClick={() => { toggleNetworkDrawer(); setMobileMenuAnchor(null); }}
              disabled={!agentNetwork}
            >
              <ListItemIcon><AccountTree fontSize="small" /></ListItemIcon>
              <ListItemText>Network View</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => { toggleDebugDrawer(); setMobileMenuAnchor(null); }}>
              <ListItemIcon>
                <Badge badgeContent={debugUnreadCount} color="error" max={99}>
                  <BugReport fontSize="small" />
                </Badge>
              </ListItemIcon>
              <ListItemText>Debug Monitor</ListItemText>
            </MenuItem>
            {userRole === 'admin' && (
              <MenuItem onClick={() => { toggleAdminDrawer(); setMobileMenuAnchor(null); }}>
                <ListItemIcon><AdminPanelSettings fontSize="small" /></ListItemIcon>
                <ListItemText>Admin Console</ListItemText>
              </MenuItem>
            )}
            <Box sx={{ px: 2, py: 1 }}>
              <UserButton
                appearance={{
                  elements: { avatarBox: { width: 32, height: 32 } },
                }}
              />
            </Box>
          </Menu>
        )}
      </Toolbar>
    </AppBar>
  );
}
