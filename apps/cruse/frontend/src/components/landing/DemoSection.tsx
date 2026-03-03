'use client';

import { Box, Typography } from '@mui/material';
import { motion } from 'framer-motion';

const VIDEO_URL = '/demo.mp4';

const spring = { type: 'spring' as const, stiffness: 300, damping: 30 };

export function DemoSection() {
  return (
    <Box
      sx={{
        py: { xs: 10, md: 14 },
        px: 3,
        background: 'linear-gradient(180deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}
    >
      {/* Section heading */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        transition={{ ...spring }}
      >
        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            textAlign: 'center',
            color: '#f1f5f9',
            mb: 1.5,
          }}
        >
          See CRUSE in Action
        </Typography>
        <Typography
          variant="body1"
          sx={{
            textAlign: 'center',
            color: '#94a3b8',
            maxWidth: 480,
            mx: 'auto',
            mb: 6,
          }}
        >
          Watch how multi-agent AI orchestration comes to life with real-time
          streaming and dynamic interfaces.
        </Typography>
      </motion.div>

      {/* Browser frame */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true, margin: '-50px' }}
        transition={{ ...spring }}
        style={{
          width: '100%',
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <Box
          className="browser-frame"
          sx={{
            width: { xs: '95%', md: '80%', lg: '60%' },
            maxWidth: 900,
          }}
        >
          {/* Browser chrome */}
          <Box className="browser-chrome">
            <span className="browser-dot" />
            <span className="browser-dot" />
            <span className="browser-dot" />
            <Box
              sx={{
                ml: 2,
                flex: 1,
                height: 28,
                borderRadius: 1.5,
                background: 'rgba(255,255,255,0.06)',
                display: 'flex',
                alignItems: 'center',
                px: 1.5,
              }}
            >
              <Typography
                variant="caption"
                sx={{ color: '#64748b', fontSize: 11 }}
              >
                cruse.app
              </Typography>
            </Box>
          </Box>

          {/* Video */}
          <Box sx={{ position: 'relative', width: '100%' }}>
            <video
              controls
              playsInline
              style={{
                width: '100%',
                display: 'block',
              }}
            >
              <source src={VIDEO_URL} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          </Box>
        </Box>
      </motion.div>
    </Box>
  );
}
