'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { Box, Typography, IconButton, Button } from '@mui/material';
import { Close as CloseIcon, CheckCircle as CheckIcon, Send as SendIcon } from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useCruseStore } from '@/store/cruseStore';
import { DynamicIcon } from '@/components/widget/DynamicIcon';
import { SchemaForm } from '@/components/widget/SchemaForm';

interface WidgetCardProps {
  onSubmit?: () => void;
}

export function WidgetCard({ onSubmit }: WidgetCardProps = {}) {
  const widgetSchema = useCruseStore((s) => s.widgetSchema);
  const widgetFormData = useCruseStore((s) => s.widgetFormData);
  const widgetSubmitted = useCruseStore((s) => s.widgetSubmitted);
  const setWidgetSchema = useCruseStore((s) => s.setWidgetSchema);
  const setWidgetFormData = useCruseStore((s) => s.setWidgetFormData);
  const setWidgetSubmitted = useCruseStore((s) => s.setWidgetSubmitted);
  const [showSuccess, setShowSuccess] = useState(false);
  const lastColorRef = useRef('#3b82f6');
  const dismissTimerRef = useRef<ReturnType<typeof setTimeout>>();

  // Show success overlay briefly when form is submitted, then dismiss the widget
  useEffect(() => {
    if (widgetSubmitted) {
      setShowSuccess(true);
      setWidgetSubmitted(false);
      dismissTimerRef.current = setTimeout(() => {
        setShowSuccess(false);
        setWidgetSchema(null);
      }, 1800);
    }
  }, [widgetSubmitted, setWidgetSubmitted, setWidgetSchema]);

  // Clean up timer on unmount only
  useEffect(() => {
    return () => {
      if (dismissTimerRef.current) clearTimeout(dismissTimerRef.current);
    };
  }, []);

  const handleChange = useCallback(
    (formData: Record<string, unknown>) => {
      setWidgetFormData(formData);
    },
    [setWidgetFormData]
  );

  if (!widgetSchema) return null;

  // Handle legacy HTML content — wrap in a <form> so InputBar can scrape
  // values with new FormData(), exactly like the original Flask implementation.
  if ('_html' in widgetSchema) {
    return (
      <Box sx={{ p: 2 }}>
        <form
          id="cruse-legacy-form"
          onSubmit={(e) => e.preventDefault()}
          dangerouslySetInnerHTML={{ __html: (widgetSchema as any)._html }}
          style={{ all: 'initial', fontFamily: 'inherit' }}
        />
      </Box>
    );
  }

  const { title, description, icon, color, schema } = widgetSchema;
  const headerColor = color || '#3b82f6';
  lastColorRef.current = headerColor;

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3 }}
      style={{
        borderRadius: 16,
        boxShadow: `0 4px 24px ${headerColor}40, 0 0 48px ${headerColor}20`,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Colored header */}
      <Box
        sx={{
          background: `linear-gradient(135deg, ${headerColor}, ${headerColor}dd)`,
          p: 2.5,
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          borderRadius: '16px 16px 0 0',
          position: 'relative',
        }}
      >
        <motion.div
          initial={{ scale: 0, rotate: -90 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ type: 'spring', stiffness: 400, damping: 15, delay: 0.2 }}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}
        >
          <DynamicIcon name={icon} color="white" size={32} />
        </motion.div>
        <Box sx={{ flex: 1 }}>
          <Typography variant="subtitle1" sx={{ color: 'white', fontWeight: 700 }}>
            {title || 'Widget'}
          </Typography>
          {description && (
            <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }}>
              {description}
            </Typography>
          )}
        </Box>
        <IconButton
          size="small"
          onClick={() => setWidgetSchema(null)}
          sx={{ color: 'rgba(255,255,255,0.7)', '&:hover': { color: 'white' } }}
        >
          <CloseIcon fontSize="small" />
        </IconButton>
      </Box>

      {/* Form body */}
      <Box sx={{ p: 2, bgcolor: 'background.paper', borderRadius: '0 0 16px 16px' }}>
        {schema ? (
          <>
            <SchemaForm schema={schema} formData={widgetFormData} onChange={handleChange} />
            {onSubmit ? (
              <Button
                variant="contained"
                endIcon={<SendIcon />}
                onClick={onSubmit}
                fullWidth
                sx={{ mt: 2 }}
              >
                Submit
              </Button>
            ) : (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Fill out the form above, then use the chat input to send your message.
              </Typography>
            )}
          </>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No form schema available.
          </Typography>
        )}
      </Box>

      {/* Success overlay */}
      <AnimatePresence>
        {showSuccess && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              background: `${lastColorRef.current}eb`,
              borderRadius: 16,
              zIndex: 10,
            }}
          >
            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: 'spring', stiffness: 300, damping: 15 }}
            >
              <CheckIcon sx={{ fontSize: 56, color: 'white' }} />
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <Typography variant="h6" sx={{ color: 'white', fontWeight: 700, mt: 1 }}>
                Form Sent!
              </Typography>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
