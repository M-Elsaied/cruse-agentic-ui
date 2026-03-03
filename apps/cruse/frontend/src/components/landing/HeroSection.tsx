'use client';

import { Box, Typography, Button } from '@mui/material';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { FloatingOrbs, LogoMark } from './WelcomeHero';

const spring = { type: 'spring' as const, stiffness: 300, damping: 30 };

export function HeroSection() {
  return (
    <Box
      sx={{
        position: 'relative',
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
      }}
    >
      {/* Background video layer */}
      <video
        autoPlay
        muted
        loop
        playsInline
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          zIndex: 0,
          pointerEvents: 'none',
        }}
      >
        <source src="/demo.mp4" type="video/mp4" />
      </video>

      {/* Dark gradient overlay / scrim */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background:
            'radial-gradient(ellipse at 50% 50%, rgba(15, 23, 42, 0.7) 0%, rgba(15, 23, 42, 0.55) 50%, rgba(15, 23, 42, 0.75) 100%)',
          zIndex: 1,
          pointerEvents: 'none',
        }}
      />

      {/* Floating orbs */}
      <FloatingOrbs darkMode={true} />

      {/* Text content */}
      <Box
        sx={{
          position: 'relative',
          zIndex: 3,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 2,
          px: 3,
          textAlign: 'center',
        }}
      >
        {/* Logo */}
        <motion.div
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ ...spring, delay: 0.1 }}
          style={{ transform: 'scale(1.5)' }}
        >
          <LogoMark />
        </motion.div>

        {/* Headline */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...spring, delay: 0.3 }}
        >
          <Typography
            variant="h2"
            sx={{
              fontWeight: 800,
              fontSize: { xs: '2rem', md: '2.5rem', lg: '3rem' },
              lineHeight: 1.1,
              background: 'linear-gradient(90deg, #3b82f6, #8b5cf6, #3b82f6)',
              backgroundSize: '200% auto',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              animation: 'shimmer 4s linear infinite',
              maxWidth: 700,
            }}
          >
            Multi-Agent AI, Orchestrated Beautifully
          </Typography>
        </motion.div>

        {/* Subtitle */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...spring, delay: 0.5 }}
        >
          <Typography
            variant="body1"
            sx={{
              color: '#94a3b8',
              fontWeight: 400,
              maxWidth: 520,
              lineHeight: 1.6,
            }}
          >
            Build, visualize, and orchestrate teams of AI agents with an
            intuitive, real-time interface.
          </Typography>
        </motion.div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...spring, delay: 0.7 }}
        >
          <Link href="/sign-up" style={{ textDecoration: 'none' }}>
            <Button
              variant="contained"
              size="large"
              sx={{
                background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                textTransform: 'none',
                fontWeight: 600,
                fontSize: '1.1rem',
                borderRadius: 3,
                px: 5,
                py: 1.5,
                '&:hover': {
                  background: 'linear-gradient(135deg, #2563eb, #7c3aed)',
                  boxShadow: '0 8px 30px rgba(59,130,246,0.5)',
                  transform: 'translateY(-2px)',
                },
                transition: 'all 0.3s ease',
              }}
            >
              Get Started
            </Button>
          </Link>
        </motion.div>
      </Box>
    </Box>
  );
}
