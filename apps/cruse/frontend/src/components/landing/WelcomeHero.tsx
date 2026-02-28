'use client';

import { Box, Typography } from '@mui/material';
import { Hub, Psychology, Widgets, Speed } from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useCruseStore } from '@/store/cruseStore';

const spring = { type: 'spring' as const, stiffness: 300, damping: 30 };

const orbConfigs = [
  { size: 260, x: '-15%', y: '-10%', color1: 'rgba(59,130,246,0.15)', color2: 'transparent', duration: 20 },
  { size: 200, x: '60%', y: '-20%', color1: 'rgba(139,92,246,0.12)', color2: 'transparent', duration: 25 },
  { size: 180, x: '20%', y: '60%', color1: 'rgba(59,130,246,0.10)', color2: 'transparent', duration: 18 },
];

const features = [
  {
    icon: Psychology,
    title: 'Multi-Agent AI',
    caption: 'Teams of specialized agents collaborate to solve your tasks',
  },
  {
    icon: Widgets,
    title: 'Dynamic Widgets',
    caption: 'Interactive forms and controls generated in real-time',
  },
  {
    icon: Speed,
    title: 'Live Streaming',
    caption: 'Watch agents think and respond with real-time streaming',
  },
];

function FloatingOrbs({ darkMode }: { darkMode: boolean }) {
  return (
    <>
      {orbConfigs.map((orb, i) => (
        <motion.div
          key={i}
          animate={{
            scale: [1, 1.15, 0.95, 1.05, 1],
            x: [0, 20, -15, 10, 0],
            y: [0, -15, 20, -10, 0],
          }}
          transition={{
            duration: orb.duration,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
          style={{
            position: 'absolute',
            left: orb.x,
            top: orb.y,
            width: orb.size,
            height: orb.size,
            borderRadius: '50%',
            background: `radial-gradient(circle, ${orb.color1}, ${orb.color2})`,
            filter: 'blur(60px)',
            opacity: darkMode ? 1 : 0.7,
            pointerEvents: 'none',
          }}
        />
      ))}
    </>
  );
}

function LogoMark() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.5 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ ...spring, delay: 0.1 }}
      style={{ position: 'relative', display: 'inline-flex' }}
    >
      {/* Pulsing glow */}
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
          width: 80,
          height: 80,
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Hub sx={{ fontSize: 40, color: 'white' }} />
      </motion.div>

      {/* Orbiting dot */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
        style={{
          position: 'absolute',
          inset: -8,
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: '#3b82f6',
            boxShadow: '0 0 8px rgba(59,130,246,0.6)',
          }}
        />
      </motion.div>
    </motion.div>
  );
}

function FeatureCard({
  icon: Icon,
  title,
  caption,
  index,
  darkMode,
}: {
  icon: typeof Psychology;
  title: string;
  caption: string;
  index: number;
  darkMode: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ ...spring, delay: 0.6 + index * 0.12 }}
    >
      <Box
        sx={{
          p: 2.5,
          borderRadius: 3,
          background: darkMode ? 'rgba(255,255,255,0.04)' : 'rgba(255,255,255,0.6)',
          backdropFilter: 'blur(12px)',
          border: '1px solid',
          borderColor: darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
          transition: 'all 0.25s ease',
          cursor: 'default',
          textAlign: 'center',
          maxWidth: 200,
          '&:hover': {
            transform: 'translateY(-2px)',
            borderColor: 'rgba(59,130,246,0.4)',
            boxShadow: '0 4px 20px rgba(59,130,246,0.15)',
          },
        }}
      >
        <Box
          sx={{
            width: 44,
            height: 44,
            borderRadius: 2,
            background: 'linear-gradient(135deg, rgba(59,130,246,0.15), rgba(139,92,246,0.15))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mx: 'auto',
            mb: 1.5,
          }}
        >
          <Icon sx={{ fontSize: 24, color: '#3b82f6' }} />
        </Box>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
          {title}
        </Typography>
        <Typography variant="caption" sx={{ color: 'text.secondary', lineHeight: 1.4 }}>
          {caption}
        </Typography>
      </Box>
    </motion.div>
  );
}

export function WelcomeHero() {
  const darkMode = useCruseStore((s) => s.darkMode);

  return (
    <Box
      sx={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <FloatingOrbs darkMode={darkMode} />

      <Box
        sx={{
          position: 'relative',
          zIndex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 2.5,
          px: 3,
        }}
      >
        <LogoMark />

        {/* Title with shimmer */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...spring, delay: 0.25 }}
        >
          <Typography
            variant="h3"
            sx={{
              fontWeight: 700,
              background: 'linear-gradient(90deg, #3b82f6, #8b5cf6, #3b82f6)',
              backgroundSize: '200% auto',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              animation: 'shimmer 4s linear infinite',
            }}
          >
            Welcome to CRUSE
          </Typography>
        </motion.div>

        {/* Subtitle */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...spring, delay: 0.35 }}
        >
          <Typography
            variant="body1"
            sx={{ color: 'text.secondary', textAlign: 'center', maxWidth: 420 }}
          >
            Your interactive playground for multi-agent AI networks.
            Select an agent network above to begin.
          </Typography>
        </motion.div>

        {/* Gradient divider */}
        <motion.div
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 0.6, delay: 0.45, ease: 'easeOut' }}
          style={{ originX: 0.5 }}
        >
          <Box
            sx={{
              width: 60,
              height: 2,
              borderRadius: 1,
              background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
            }}
          />
        </motion.div>

        {/* Feature cards */}
        <Box
          sx={{
            display: 'flex',
            gap: 2,
            flexWrap: 'wrap',
            justifyContent: 'center',
            mt: 1,
          }}
        >
          {features.map((feature, i) => (
            <FeatureCard
              key={feature.title}
              icon={feature.icon}
              title={feature.title}
              caption={feature.caption}
              index={i}
              darkMode={darkMode}
            />
          ))}
        </Box>

        {/* Hint text */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 1.2 }}
        >
          <Typography variant="body2" sx={{ color: 'text.secondary', opacity: 0.6 }}>
            Use the dropdown above to get started
          </Typography>
        </motion.div>
      </Box>
    </Box>
  );
}
