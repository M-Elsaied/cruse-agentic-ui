'use client';

import { Box, Typography } from '@mui/material';
import { Psychology, Widgets, Speed, AccountTree } from '@mui/icons-material';
import { motion } from 'framer-motion';

const features = [
  {
    icon: Psychology,
    title: 'Multi-Agent Orchestration',
    caption: 'Teams of specialized AI agents collaborate seamlessly using the AAOSA protocol to solve complex tasks.',
  },
  {
    icon: Widgets,
    title: 'Dynamic Widgets',
    caption: 'Interactive forms, sliders, and controls generated in real-time based on agent responses.',
  },
  {
    icon: Speed,
    title: 'Live Streaming',
    caption: 'Watch agents think and respond with real-time token streaming and activity indicators.',
  },
  {
    icon: AccountTree,
    title: 'Network Visualization',
    caption: 'Explore agent hierarchies and communication flows with interactive network graphs.',
  },
];

const spring = { type: 'spring' as const, stiffness: 300, damping: 30 };

export function FeaturesSection() {
  return (
    <Box
      sx={{
        py: { xs: 10, md: 14 },
        px: 3,
        background: '#0f172a',
        position: 'relative',
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
          Built for the Future of AI
        </Typography>
        <Typography
          variant="body1"
          sx={{
            textAlign: 'center',
            color: '#94a3b8',
            maxWidth: 500,
            mx: 'auto',
            mb: 6,
          }}
        >
          Everything you need to orchestrate, visualize, and interact with
          multi-agent AI systems.
        </Typography>
      </motion.div>

      {/* Feature cards grid */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            sm: 'repeat(2, 1fr)',
            md: 'repeat(4, 1fr)',
          },
          gap: 3,
          maxWidth: 1200,
          mx: 'auto',
        }}
      >
        {features.map((feature, i) => (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ ...spring, delay: i * 0.15 }}
          >
            <Box
              sx={{
                p: 3.5,
                borderRadius: 3,
                background: 'rgba(255,255,255,0.04)',
                backdropFilter: 'blur(12px)',
                border: '1px solid rgba(255,255,255,0.06)',
                textAlign: 'center',
                maxWidth: 280,
                mx: 'auto',
                height: '100%',
                transition: 'all 0.25s ease',
                cursor: 'default',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  borderColor: 'rgba(59,130,246,0.4)',
                  boxShadow: '0 8px 30px rgba(59,130,246,0.15)',
                },
              }}
            >
              <Box
                sx={{
                  width: 56,
                  height: 56,
                  borderRadius: 2.5,
                  background: 'linear-gradient(135deg, rgba(59,130,246,0.15), rgba(139,92,246,0.15))',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mx: 'auto',
                  mb: 2,
                }}
              >
                <feature.icon sx={{ fontSize: 28, color: '#3b82f6' }} />
              </Box>
              <Typography
                variant="subtitle1"
                sx={{ fontWeight: 600, color: '#f1f5f9', mb: 1 }}
              >
                {feature.title}
              </Typography>
              <Typography
                variant="body2"
                sx={{ color: '#94a3b8', lineHeight: 1.6 }}
              >
                {feature.caption}
              </Typography>
            </Box>
          </motion.div>
        ))}
      </Box>
    </Box>
  );
}
