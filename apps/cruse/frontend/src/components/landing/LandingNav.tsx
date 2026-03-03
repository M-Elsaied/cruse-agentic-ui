'use client';

import { useState, useEffect } from 'react';
import { AppBar, Toolbar, Button, Typography, Box } from '@mui/material';
import { Hub } from '@mui/icons-material';
import { motion } from 'framer-motion';
import Link from 'next/link';

export function LandingNav() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const container = document.getElementById('landing-scroll-container');
    if (!container) return;
    const onScroll = () => setScrolled(container.scrollTop > 50);
    container.addEventListener('scroll', onScroll);
    return () => container.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 1100 }}
    >
      <AppBar
        position="static"
        elevation={0}
        sx={{
          background: scrolled
            ? 'rgba(15, 23, 42, 0.85)'
            : 'transparent',
          backdropFilter: scrolled ? 'blur(20px)' : 'none',
          borderBottom: scrolled
            ? '1px solid rgba(255,255,255,0.08)'
            : '1px solid transparent',
          transition: 'all 0.3s ease',
        }}
      >
        <Toolbar sx={{ justifyContent: 'space-between', px: { xs: 2, md: 4 } }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Hub sx={{ color: '#3b82f6', fontSize: 28 }} />
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                letterSpacing: '0.05em',
              }}
            >
              CRUSE
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Link href="/sign-in" style={{ textDecoration: 'none' }}>
              <Button
                sx={{
                  color: '#94a3b8',
                  textTransform: 'none',
                  fontWeight: 500,
                  display: { xs: 'none', sm: 'inline-flex' },
                  '&:hover': { color: '#f1f5f9' },
                }}
              >
                Sign In
              </Button>
            </Link>
            <Link href="/sign-up" style={{ textDecoration: 'none' }}>
              <Button
                variant="contained"
                sx={{
                  background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                  textTransform: 'none',
                  fontWeight: 600,
                  borderRadius: 2,
                  px: 3,
                  '&:hover': {
                    background: 'linear-gradient(135deg, #2563eb, #7c3aed)',
                    boxShadow: '0 4px 20px rgba(59,130,246,0.4)',
                  },
                }}
              >
                Get Started
              </Button>
            </Link>
          </Box>
        </Toolbar>
      </AppBar>
    </motion.div>
  );
}
