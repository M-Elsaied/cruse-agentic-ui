'use client';

import { AnimatePresence, motion } from 'framer-motion';
import { useCruseStore } from '@/store/cruseStore';
import { CssDoodleBackground } from '@/components/theme/CssDoodleBackground';
import { GradientBackground } from '@/components/theme/GradientBackground';

/**
 * Renders the current background theme with crossfade transitions.
 * Supports both css-doodle dynamic backgrounds and CSS gradient backgrounds.
 */
export function BackgroundEngine() {
  const theme = useCruseStore((s) => s.theme);
  const darkMode = useCruseStore((s) => s.darkMode);

  // Inline SVG noise texture as data URI — adds tactile grain with zero network requests
  const noiseDataUri = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.5'/%3E%3C/svg%3E")`;

  // Default background when no theme is set
  if (!theme) {
    return (
      <div
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 0,
          background: darkMode
            ? 'linear-gradient(135deg, #0f172a 0%, #131d35 50%, #1e293b 100%)'
            : 'linear-gradient(135deg, #f8fafc 0%, #eef2f7 50%, #e2e8f0 100%)',
          transition: 'background 0.5s ease-in-out',
        }}
      >
        {/* Mesh gradient overlay */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: darkMode
              ? `radial-gradient(ellipse 80% 60% at 20% 50%, rgba(59,130,246,0.08) 0%, transparent 70%),
                 radial-gradient(ellipse 60% 80% at 80% 20%, rgba(139,92,246,0.06) 0%, transparent 70%),
                 radial-gradient(ellipse 70% 50% at 50% 80%, rgba(59,130,246,0.05) 0%, transparent 70%)`
              : `radial-gradient(ellipse 80% 60% at 20% 50%, rgba(59,130,246,0.06) 0%, transparent 70%),
                 radial-gradient(ellipse 60% 80% at 80% 20%, rgba(139,92,246,0.05) 0%, transparent 70%),
                 radial-gradient(ellipse 70% 50% at 50% 80%, rgba(59,130,246,0.04) 0%, transparent 70%)`,
            animation: 'meshDrift 30s ease-in-out infinite alternate',
          }}
        />
        {/* Noise texture overlay */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: noiseDataUri,
            backgroundRepeat: 'repeat',
            opacity: darkMode ? 0.03 : 0.02,
            pointerEvents: 'none',
          }}
        />
      </div>
    );
  }

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={JSON.stringify(theme).slice(0, 100)}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 1 }}
        style={{ position: 'absolute', inset: 0, zIndex: 0 }}
      >
        {theme.type === 'css-doodle' ? (
          <CssDoodleBackground theme={theme} />
        ) : (
          <GradientBackground theme={theme} />
        )}
      </motion.div>
    </AnimatePresence>
  );
}
