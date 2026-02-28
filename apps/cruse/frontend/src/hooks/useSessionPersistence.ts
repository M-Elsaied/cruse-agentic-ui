import { useEffect } from 'react';
import { useCruseStore } from '@/store/cruseStore';

const STORAGE_KEY = 'cruse-session';

interface PersistedState {
  darkMode: boolean;
  agentNetwork: string | null;
}

/**
 * Persists selected dark mode and last-used agent network to localStorage.
 * Session IDs are not persisted because agent sessions are ephemeral.
 */
export function useSessionPersistence() {
  const darkMode = useCruseStore((s) => s.darkMode);
  const agentNetwork = useCruseStore((s) => s.agentNetwork);
  const toggleDarkMode = useCruseStore((s) => s.toggleDarkMode);
  const setAgentNetwork = useCruseStore((s) => s.setAgentNetwork);

  // Restore on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) return;

      const parsed: PersistedState = JSON.parse(stored);

      if (typeof parsed.darkMode === 'boolean' && parsed.darkMode !== darkMode) {
        toggleDarkMode();
      }

      // We don't auto-restore agentNetwork because the session is gone,
      // but we could use it as a hint for the dropdown.
    } catch {
      // Ignore parse errors
    }
    // Only run once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Save on change
  useEffect(() => {
    try {
      const state: PersistedState = { darkMode, agentNetwork };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      // localStorage may be unavailable
    }
  }, [darkMode, agentNetwork]);
}
