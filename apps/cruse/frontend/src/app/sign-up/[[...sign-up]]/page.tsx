'use client';

import { SignUp } from '@clerk/nextjs';
import { Box, Typography } from '@mui/material';
import { Hub } from '@mui/icons-material';
import { useCruseStore } from '@/store/cruseStore';

export default function SignUpPage() {
  const darkMode = useCruseStore((s) => s.darkMode);

  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: darkMode ? '#0f172a' : '#f8fafc',
        gap: 3,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Hub sx={{ color: '#3b82f6', fontSize: 36 }} />
        <Typography
          variant="h4"
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
      <SignUp
        appearance={{
          elements: {
            rootBox: { width: '100%', maxWidth: 400 },
            card: {
              background: darkMode ? '#1e293b' : '#ffffff',
              borderRadius: 16,
              border: darkMode
                ? '1px solid rgba(255,255,255,0.08)'
                : '1px solid rgba(0,0,0,0.08)',
            },
          },
        }}
      />
    </Box>
  );
}
