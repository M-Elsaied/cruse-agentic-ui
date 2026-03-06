'use client';

import { Box, IconButton, Tooltip } from '@mui/material';
import { ThumbUp, ThumbUpOutlined, ThumbDown, ThumbDownOutlined } from '@mui/icons-material';
import { useCruseStore } from '@/store/cruseStore';
import { useAuthenticatedFetch } from '@/utils/api';
import type { ChatMessage } from '@/store/cruseStore';

interface MessageFeedbackButtonsProps {
  message: ChatMessage;
}

export function MessageFeedbackButtons({ message }: MessageFeedbackButtonsProps) {
  const feedbackRatings = useCruseStore((s) => s.feedbackRatings);
  const setFeedbackRating = useCruseStore((s) => s.setFeedbackRating);
  const removeFeedbackRating = useCruseStore((s) => s.removeFeedbackRating);
  const openFeedbackDialog = useCruseStore((s) => s.openFeedbackDialog);
  const { authFetch, API_BASE } = useAuthenticatedFetch();

  const currentRating = feedbackRatings[message.id];
  const dbId = message.dbId;

  const handleRate = async (rating: 1 | -1) => {
    if (!dbId) return;

    if (currentRating === rating) {
      // Un-rate: clicking same thumb again
      removeFeedbackRating(message.id);
      try {
        await authFetch(`${API_BASE}/api/messages/${dbId}/rating`, { method: 'DELETE' });
      } catch {
        // Best-effort
      }
      return;
    }

    setFeedbackRating(message.id, rating);
    try {
      await authFetch(`${API_BASE}/api/messages/${dbId}/rating`, {
        method: 'POST',
        body: JSON.stringify({ rating }),
      });
    } catch {
      // Best-effort
    }

    if (rating === -1) {
      openFeedbackDialog(message);
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        gap: 0.25,
        mt: 0.5,
        opacity: currentRating ? 0.9 : 0.3,
        transition: 'opacity 0.2s',
        '&:hover': { opacity: 1 },
      }}
    >
      <Tooltip title="Helpful" placement="bottom" arrow>
        <IconButton
          size="small"
          onClick={() => handleRate(1)}
          sx={{
            p: 0.5,
            color: currentRating === 1 ? '#22c55e' : 'inherit',
          }}
        >
          {currentRating === 1 ? <ThumbUp sx={{ fontSize: 16 }} /> : <ThumbUpOutlined sx={{ fontSize: 16 }} />}
        </IconButton>
      </Tooltip>
      <Tooltip title="Not helpful" placement="bottom" arrow>
        <IconButton
          size="small"
          onClick={() => handleRate(-1)}
          sx={{
            p: 0.5,
            color: currentRating === -1 ? '#f97316' : 'inherit',
          }}
        >
          {currentRating === -1 ? <ThumbDown sx={{ fontSize: 16 }} /> : <ThumbDownOutlined sx={{ fontSize: 16 }} />}
        </IconButton>
      </Tooltip>
    </Box>
  );
}