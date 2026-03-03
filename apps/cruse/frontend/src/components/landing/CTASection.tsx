'use client';

import { Box, Typography, Button } from '@mui/material';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { FloatingOrbs } from './WelcomeHero';

const spring = { type: 'spring' as const, stiffness: 300, damping: 30 };

export function CTASection() {
  return (
    <Box
      sx={{
        py: { xs: 12, md: 16 },
        px: 3,
        position: 'relative',
        overflow: 'hidden',
        background:
          'radial-gradient(ellipse at center, rgba(59,130,246,0.08) 0%, #0f172a 70%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <FloatingOrbs darkMode={true} />

      <Box sx={{ position: 'relative', zIndex: 1, textAlign: 'center' }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ ...spring }}
        >
          <Typography
            variant="h3"
            sx={{
              fontWeight: 800,
              color: '#f1f5f9',
              mb: 2,
              fontSize: { xs: '2rem', md: '3rem' },
            }}
          >
            Ready to Orchestrate?
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: '#94a3b8',
              maxWidth: 440,
              mx: 'auto',
              mb: 4,
              lineHeight: 1.6,
            }}
          >
            Start building multi-agent AI workflows in minutes. No credit card
            required.
          </Typography>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-50px' }}
          transition={{ ...spring, delay: 0.2 }}
        >
          {/* Pulsing glow button */}
          <motion.div
            animate={{
              boxShadow: [
                '0 0 20px rgba(59,130,246,0.3), 0 0 60px rgba(139,92,246,0.1)',
                '0 0 30px rgba(59,130,246,0.5), 0 0 80px rgba(139,92,246,0.2)',
                '0 0 20px rgba(59,130,246,0.3), 0 0 60px rgba(139,92,246,0.1)',
              ],
            }}
            transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
            style={{ display: 'inline-block', borderRadius: 12 }}
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
                  px: 6,
                  py: 1.5,
                  '&:hover': {
                    background: 'linear-gradient(135deg, #2563eb, #7c3aed)',
                  },
                }}
              >
                Get Started Free
              </Button>
            </Link>
          </motion.div>

          <Typography
            variant="body2"
            sx={{
              color: '#64748b',
              mt: 2,
            }}
          >
            No credit card required
          </Typography>
        </motion.div>
      </Box>
    </Box>
  );
}
