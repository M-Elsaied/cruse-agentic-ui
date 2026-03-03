'use client';

import { Box } from '@mui/material';
import { LandingNav } from './LandingNav';
import { HeroSection } from './HeroSection';
import { FeaturesSection } from './FeaturesSection';

import { CTASection } from './CTASection';

export function LandingPage() {
  return (
    <Box
      id="landing-scroll-container"
      className="landing-scroll"
      data-theme="dark"
      sx={{
        bgcolor: '#0f172a',
        color: '#f1f5f9',
      }}
    >
      <LandingNav />
      <HeroSection />
      <FeaturesSection />
      <CTASection />
    </Box>
  );
}
