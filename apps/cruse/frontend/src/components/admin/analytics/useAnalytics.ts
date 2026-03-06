'use client';

import { useCallback, useEffect, useState } from 'react';
import { useAuthenticatedFetch } from '@/utils/api';

export interface AnalyticsOverview {
  total_requests: number;
  unique_users: number;
  avg_latency_ms: number;
  error_count: number;
  error_rate: number;
  satisfaction_score: number;
  open_reports: number;
  period_days: number;
  prev_total_requests: number;
  prev_unique_users: number;
  prev_error_rate: number;
}

export interface TimeSeriesPoint {
  date: string;
  count: number;
  error_count: number;
}

export interface ActiveUsersPoint {
  date: string;
  count: number;
}

export interface NetworkScorecard {
  network: string;
  request_count: number;
  avg_latency_ms: number;
  error_rate: number;
  satisfaction_score: number;
  avg_depth: number;
}

export interface AnalyticsData {
  overview: AnalyticsOverview;
  requests_over_time: TimeSeriesPoint[];
  active_users_over_time: ActiveUsersPoint[];
  network_scorecard: NetworkScorecard[];
}

export interface UserBreakdown {
  user_id: string;
  email: string | null;
  name: string | null;
  request_count: number;
  conversation_count: number;
  avg_latency_ms: number;
  last_active: string | null;
}

export interface UserBreakdownData {
  users: UserBreakdown[];
  total: number;
}

export function useAnalytics() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [periodDays, setPeriodDays] = useState(30);
  const { authFetch, API_BASE } = useAuthenticatedFetch();

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await authFetch(`${API_BASE}/api/admin/analytics?period_days=${periodDays}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  }, [authFetch, API_BASE, periodDays]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  return { data, loading, error, periodDays, setPeriodDays, refresh: fetchAnalytics };
}
