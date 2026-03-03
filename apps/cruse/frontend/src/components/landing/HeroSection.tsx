'use client';

import { useState } from 'react';
import { Box, Typography, Button } from '@mui/material';
import { KeyboardArrowDown } from '@mui/icons-material';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { FloatingOrbs, LogoMark } from './WelcomeHero';

const spring = { type: 'spring' as const, stiffness: 300, damping: 30 };

const VIDEO_URL =
  'https://github.com/user-attachments/assets/8cf88c66-c8c4-42dd-972b-df086c228ab9';

export function HeroSection() {
  const [videoFailed, setVideoFailed] = useState(false);

  return (
    <Box
      sx={{
        position: 'relative',
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
      }}
    >
      {/* Video background */}
      {!videoFailed && (
        <video
          autoPlay
          muted
          loop
          playsInline
          onError={() => setVideoFailed(true)}
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            zIndex: 0,
          }}
        >
          <source src={VIDEO_URL} type="video/mp4" />
        </video>
      )}

      {/* Gradient overlay */}
      <div className="hero-video-overlay" />

      {/* Floating orbs */}
      <FloatingOrbs darkMode={true} />

      {/* Content */}
      <Box
        sx={{
          position: 'relative',
          zIndex: 2,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 3,
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
              fontSize: { xs: '2.5rem', md: '4rem' },
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
            variant="h6"
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
          <Button
            component={Link}
            href="/sign-up"
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
        </motion.div>
      </Box>

      {/* Scroll indicator */}
      <Box
        sx={{
          position: 'absolute',
          bottom: 32,
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 2,
        }}
      >
        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        >
          <KeyboardArrowDown sx={{ fontSize: 32, color: '#94a3b8', opacity: 0.6 }} />
        </motion.div>
      </Box>
    </Box>
  );
}
