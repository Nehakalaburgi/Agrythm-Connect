import { useState } from 'react';

/**
 * Custom hook for managing dashboard telemetry and metrics state
 */
export const useDashboardData = () => {
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState({
    activeSensors: 48,
    totalAreaCovered: '1,240 Ha',
    aiConfidenceScore: '98.4%',
    systemStatus: 'Operational',
  });

  return {
    metrics,
    loading,
    setLoading,
    setMetrics,
  };
};
