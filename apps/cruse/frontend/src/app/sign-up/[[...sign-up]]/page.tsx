'use client';

import { SignUp } from '@clerk/nextjs';
import { Box, Typography } from '@mui/material';
import { Hub, Psychology, Widgets, Speed } from '@mui/icons-material';
import { motion } from 'framer-motion';
import { FloatingOrbs } from '@/components/landing/WelcomeHero';

const spring = { type: 'spring' as const, stiffness: 300, damping: 30 };

const highlights = [
  { icon: Psychology, text: 'Multi-agent AI orchestration' },
  { icon: Widgets, text: 'Dynamic, interactive widgets' },
  { icon: Speed, text: 'Real-time streaming responses' },
];

export default function SignUpPage() {
  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        bgcolor: '#0f172a',
        overflow: 'hidden',
      }}
    >
      {/* Left branding panel */}
      <Box
        sx={{
          width: '55%',
          display: { xs: 'none', md: 'flex' },
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          overflow: 'hidden',
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        }}
      >
        <FloatingOrbs darkMode={true} />

        <Box sx={{ position: 'relative', zIndex: 1, textAlign: 'center', px: 4 }}>
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ ...spring }}
          >
            {/* Logo */}
            <motion.div
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ ...spring, delay: 0.1 }}
              style={{ display: 'inline-flex', marginBottom: 24 }}
            >
              <motion.div
                animate={{
                  boxShadow: [
                    '0 0 20px rgba(59,130,246,0.3), 0 0 60px rgba(139,92,246,0.15)',
                    '0 0 30px rgba(59,130,246,0.5), 0 0 80px rgba(139,92,246,0.25)',
                    '0 0 20px rgba(59,130,246,0.3), 0 0 60px rgba(139,92,246,0.15)',
                  ],
                }}
                transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
                style={{
                  width: 72,
                  height: 72,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Hub sx={{ fontSize: 36, color: 'white' }} />
              </motion.div>
            </motion.div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ ...spring, delay: 0.15 }}
          >
            <Typography
              variant="h3"
              sx={{
                fontWeight: 800,
                mb: 1.5,
                background: 'linear-gradient(90deg, #3b82f6, #8b5cf6, #3b82f6)',
                backgroundSize: '200% auto',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                animation: 'shimmer 4s linear infinite',
              }}
            >
              Join CRUSE
            </Typography>
            <Typography
              variant="h6"
              sx={{ color: '#94a3b8', fontWeight: 400, mb: 5 }}
            >
              Start orchestrating AI agents in minutes
            </Typography>
          </motion.div>

          {/* Mini feature highlights */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, alignItems: 'flex-start', mx: 'auto', maxWidth: 300 }}>
            {highlights.map((item, i) => (
              <motion.div
                key={item.text}
                initial={{ opacity: 0, x: -30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ ...spring, delay: 0.3 + i * 0.15 }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Box
                    sx={{
                      width: 36,
                      height: 36,
                      borderRadius: 2,
                      background: 'rgba(59,130,246,0.12)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                    }}
                  >
                    <item.icon sx={{ fontSize: 18, color: '#3b82f6' }} />
                  </Box>
                  <Typography variant="body2" sx={{ color: '#94a3b8' }}>
                    {item.text}
                  </Typography>
                </Box>
              </motion.div>
            ))}
          </Box>
        </Box>
      </Box>

      {/* Right Clerk panel */}
      <Box
        sx={{
          width: { xs: '100%', md: '45%' },
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          px: 3,
        }}
      >
        {/* Compact logo for mobile */}
        <Box
          sx={{
            display: { xs: 'flex', md: 'none' },
            alignItems: 'center',
            gap: 1,
            mb: 3,
          }}
        >
          <Hub sx={{ color: '#3b82f6', fontSize: 32 }} />
          <Typography
            variant="h5"
            sx={{
              fontWeight: 700,
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            CRUSE
          </Typography>
        </Box>

        <motion.div
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ ...spring, delay: 0.2 }}
        >
          <Box
            sx={{
              background: 'rgba(30,41,59,0.6)',
              backdropFilter: 'blur(20px)',
              borderRadius: 4,
              border: '1px solid rgba(255,255,255,0.08)',
              p: { xs: 2, sm: 3 },
            }}
          >
            <SignUp
              routing="path"
              path="/sign-up"
              appearance={{
                elements: {
                  rootBox: { width: '100%', maxWidth: 400 },
                  card: {
                    background: 'transparent',
                    boxShadow: 'none',
                    border: 'none',
                  },
                  headerTitle: { color: '#f1f5f9' },
                  headerSubtitle: { color: '#94a3b8' },
                  formFieldLabel: { color: '#94a3b8' },
                  formFieldInput: {
                    background: 'rgba(255,255,255,0.06)',
                    borderColor: 'rgba(255,255,255,0.1)',
                    color: '#f1f5f9',
                    '&:focus': {
                      borderColor: '#3b82f6',
                      boxShadow: '0 0 0 2px rgba(59,130,246,0.3)',
                    },
                  },
                  formButtonPrimary: {
                    background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #2563eb, #7c3aed)',
                    },
                  },
                  socialButtonsBlockButton: {
                    background: 'rgba(255,255,255,0.06)',
                    borderColor: 'rgba(255,255,255,0.1)',
                    color: '#f1f5f9',
                    '&:hover': {
                      background: 'rgba(255,255,255,0.1)',
                    },
                  },
                  footerActionLink: { color: '#3b82f6' },
                  dividerLine: { borderColor: 'rgba(255,255,255,0.08)' },
                  dividerText: { color: '#64748b' },
                  identityPreviewEditButton: { color: '#3b82f6' },
                  formFieldAction: { color: '#3b82f6' },
                  alertText: { color: '#f1f5f9' },
                  footerActionText: { color: '#94a3b8' },
                },
              }}
            />
          </Box>
        </motion.div>
      </Box>
    </Box>
  );
}
