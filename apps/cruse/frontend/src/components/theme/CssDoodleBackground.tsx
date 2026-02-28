'use client';

import { useEffect, useRef, useState } from 'react';
import { Box } from '@mui/material';
import type { CssDoodleTheme } from '@/types/theme';

interface CssDoodleBackgroundProps {
  theme: CssDoodleTheme;
}

/**
 * Renders a css-doodle web component as a background.
 * Dynamically loads the css-doodle library (client-only) and injects
 * the rules from the theme agent.
 */
export function CssDoodleBackground({ theme }: CssDoodleBackgroundProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loaded, setLoaded] = useState(false);

  // Load css-doodle script once
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (document.querySelector('script[data-css-doodle]')) {
      setLoaded(true);
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://unpkg.com/css-doodle@0.40.5/css-doodle.min.js';
    script.dataset.cssDoodle = 'true';
    script.onload = () => setLoaded(true);
    document.head.appendChild(script);
  }, []);

  // Render the doodle
  useEffect(() => {
    if (!loaded || !containerRef.current) return;

    // Build CSS custom properties from vars
    let varsCSS = '';
    if (theme.vars) {
      varsCSS = Object.entries(theme.vars)
        .map(([k, v]) => `${k}: ${v};`)
        .join('\n');
    }

    const doodleHTML = `<css-doodle>${varsCSS ? `:doodle { ${varsCSS} }\n` : ''}${theme.rules}</css-doodle>`;

    // Clear and inject
    containerRef.current.innerHTML = doodleHTML;

    // Trigger update on the doodle element
    const doodleEl = containerRef.current.querySelector('css-doodle') as any;
    if (doodleEl?.update) {
      doodleEl.update();
    }
  }, [loaded, theme]);

  return (
    <Box
      ref={containerRef}
      sx={{
        position: 'absolute',
        inset: 0,
        zIndex: 0,
        overflow: 'hidden',
        transition: 'opacity 1s ease-in-out',
        '& css-doodle': {
          width: '100%',
          height: '100%',
          display: 'block',
        },
      }}
    />
  );
}
