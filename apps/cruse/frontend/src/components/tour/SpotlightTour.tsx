'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { Box, Button, IconButton, Typography } from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { AnimatePresence, motion } from 'framer-motion';
import { useCruseStore } from '@/store/cruseStore';
import { tourSteps } from './tourSteps';
import type { TourPlacement } from './tourSteps';

interface TargetRect {
  top: number;
  left: number;
  width: number;
  height: number;
}

const SPOTLIGHT_PADDING = 8;
const TOOLTIP_GAP = 16;
const TOOLTIP_WIDTH = 340;

function getTargetRect(target: string | null): TargetRect | null {
  if (!target) return null;
  const el = document.querySelector(`[data-tour="${target}"]`);
  if (!el) return null;
  const rect = el.getBoundingClientRect();
  return {
    top: rect.top - SPOTLIGHT_PADDING,
    left: rect.left - SPOTLIGHT_PADDING,
    width: rect.width + SPOTLIGHT_PADDING * 2,
    height: rect.height + SPOTLIGHT_PADDING * 2,
  };
}

function computeTooltipPosition(
  targetRect: TargetRect | null,
  placement: TourPlacement,
): { top: number; left: number } {
  if (!targetRect || placement === 'center') {
    return {
      top: window.innerHeight / 2 - 100,
      left: window.innerWidth / 2 - TOOLTIP_WIDTH / 2,
    };
  }

  let top = 0;
  let left = 0;

  switch (placement) {
    case 'bottom':
      top = targetRect.top + targetRect.height + TOOLTIP_GAP;
      left = targetRect.left + targetRect.width / 2 - TOOLTIP_WIDTH / 2;
      break;
    case 'top':
      top = targetRect.top - TOOLTIP_GAP - 180;
      left = targetRect.left + targetRect.width / 2 - TOOLTIP_WIDTH / 2;
      break;
    case 'left':
      top = targetRect.top + targetRect.height / 2 - 90;
      left = targetRect.left - TOOLTIP_WIDTH - TOOLTIP_GAP;
      break;
    case 'right':
      top = targetRect.top + targetRect.height / 2 - 90;
      left = targetRect.left + targetRect.width + TOOLTIP_GAP;
      break;
  }

  // Clamp to viewport
  const margin = 16;
  left = Math.max(margin, Math.min(left, window.innerWidth - TOOLTIP_WIDTH - margin));
  top = Math.max(margin, Math.min(top, window.innerHeight - 220));

  return { top, left };
}

export function SpotlightTour() {
  const tourActive = useCruseStore((s) => s.tourActive);
  const tourStep = useCruseStore((s) => s.tourStep);
  const setTourStep = useCruseStore((s) => s.setTourStep);
  const endTour = useCruseStore((s) => s.endTour);
  const darkMode = useCruseStore((s) => s.darkMode);

  const [targetRect, setTargetRect] = useState<TargetRect | null>(null);
  const resizeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const currentStep = tourSteps[tourStep];
  const isFirstStep = tourStep === 0;
  const isLastStep = tourStep === tourSteps.length - 1;

  const measure = useCallback(() => {
    if (!tourActive) return;
    const step = tourSteps[useCruseStore.getState().tourStep];
    if (step) {
      setTargetRect(getTargetRect(step.target));
    }
  }, [tourActive]);

  // Measure on step change
  useEffect(() => {
    if (!tourActive) return;
    // Small delay to let DOM settle (e.g. after animations)
    const timer = setTimeout(measure, 50);
    return () => clearTimeout(timer);
  }, [tourStep, tourActive, measure]);

  // Re-measure on resize (debounced)
  useEffect(() => {
    if (!tourActive) return;

    const handleResize = () => {
      if (resizeTimerRef.current) clearTimeout(resizeTimerRef.current);
      resizeTimerRef.current = setTimeout(measure, 100);
    };

    const handleScroll = () => measure();

    window.addEventListener('resize', handleResize);
    window.addEventListener('scroll', handleScroll, true);
    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('scroll', handleScroll, true);
      if (resizeTimerRef.current) clearTimeout(resizeTimerRef.current);
    };
  }, [tourActive, measure]);

  // Keyboard navigation
  useEffect(() => {
    if (!tourActive) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        endTour();
      } else if (e.key === 'ArrowRight') {
        if (!isLastStep) setTourStep(tourStep + 1);
        else endTour();
      } else if (e.key === 'ArrowLeft') {
        if (!isFirstStep) setTourStep(tourStep - 1);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [tourActive, tourStep, isFirstStep, isLastStep, setTourStep, endTour]);

  if (!tourActive || !currentStep) return null;

  const tooltipPos = computeTooltipPosition(targetRect, currentStep.placement);
  const isCentered = currentStep.placement === 'center';

  return (
    <AnimatePresence>
      {tourActive && (
        <motion.div
          key="tour-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 9999,
          }}
        >
          {/* Clickable backdrop */}
          <Box
            onClick={endTour}
            sx={{
              position: 'absolute',
              inset: 0,
              zIndex: 0,
              // If there's no target, backdrop is the dimmed overlay
              bgcolor: isCentered ? 'rgba(0,0,0,0.6)' : 'transparent',
            }}
          />

          {/* Spotlight hole (only when targeting an element) */}
          {targetRect && !isCentered && (
            <motion.div
              initial={false}
              animate={{
                top: targetRect.top,
                left: targetRect.left,
                width: targetRect.width,
                height: targetRect.height,
              }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              style={{
                position: 'absolute',
                borderRadius: 12,
                boxShadow: '0 0 0 9999px rgba(0,0,0,0.6)',
                zIndex: 1,
                pointerEvents: 'none',
              }}
            />
          )}

          {/* Tooltip card */}
          <AnimatePresence mode="wait">
            <motion.div
              key={tourStep}
              initial={{ opacity: 0, y: 10, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.97 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              style={{
                position: 'absolute',
                top: tooltipPos.top,
                left: tooltipPos.left,
                width: TOOLTIP_WIDTH,
                zIndex: 2,
                pointerEvents: 'auto',
              }}
            >
              <Box
                onClick={(e) => e.stopPropagation()}
                sx={{
                  borderRadius: 3,
                  p: 3,
                  background: darkMode
                    ? 'linear-gradient(135deg, rgba(30,41,59,0.95), rgba(15,23,42,0.95))'
                    : 'linear-gradient(135deg, rgba(255,255,255,0.97), rgba(248,250,252,0.97))',
                  backdropFilter: 'blur(16px)',
                  border: '1px solid',
                  borderColor: darkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)',
                  boxShadow: darkMode
                    ? '0 20px 60px rgba(0,0,0,0.5)'
                    : '0 20px 60px rgba(0,0,0,0.15)',
                }}
              >
                {/* Close button */}
                <IconButton
                  onClick={endTour}
                  size="small"
                  sx={{
                    position: 'absolute',
                    top: 8,
                    right: 8,
                    color: darkMode ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.4)',
                  }}
                >
                  <CloseIcon fontSize="small" />
                </IconButton>

                {/* Title */}
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 700,
                    mb: 1,
                    pr: 3,
                    background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    fontSize: '1.1rem',
                  }}
                >
                  {currentStep.title}
                </Typography>

                {/* Description */}
                <Typography
                  variant="body2"
                  sx={{
                    color: darkMode ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.6)',
                    lineHeight: 1.6,
                    mb: 2.5,
                  }}
                >
                  {currentStep.description}
                </Typography>

                {/* Step dots */}
                <Box sx={{ display: 'flex', justifyContent: 'center', gap: 0.75, mb: 2 }}>
                  {tourSteps.map((_, i) => (
                    <Box
                      key={i}
                      sx={{
                        width: i === tourStep ? 20 : 6,
                        height: 6,
                        borderRadius: 3,
                        bgcolor: i === tourStep ? '#3b82f6' : darkMode ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.15)',
                        transition: 'all 0.3s ease',
                      }}
                    />
                  ))}
                </Box>

                {/* Navigation buttons */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Button
                    size="small"
                    onClick={endTour}
                    sx={{
                      textTransform: 'none',
                      color: darkMode ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.4)',
                      '&:hover': {
                        color: darkMode ? 'rgba(255,255,255,0.8)' : 'rgba(0,0,0,0.7)',
                      },
                    }}
                  >
                    Skip tour
                  </Button>

                  <Box sx={{ display: 'flex', gap: 1 }}>
                    {!isFirstStep && (
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => setTourStep(tourStep - 1)}
                        sx={{
                          textTransform: 'none',
                          borderColor: darkMode ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.15)',
                          color: darkMode ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.6)',
                        }}
                      >
                        Back
                      </Button>
                    )}
                    <Button
                      size="small"
                      variant="contained"
                      onClick={() => {
                        if (isLastStep) endTour();
                        else setTourStep(tourStep + 1);
                      }}
                      sx={{
                        textTransform: 'none',
                        background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                        '&:hover': {
                          background: 'linear-gradient(135deg, #2563eb, #7c3aed)',
                        },
                      }}
                    >
                      {isLastStep ? 'Get Started' : 'Next'}
                    </Button>
                  </Box>
                </Box>
              </Box>
            </motion.div>
          </AnimatePresence>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
