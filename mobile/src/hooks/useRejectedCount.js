import { useQuery } from '@tanstack/react-query';
import { AppState } from 'react-native';
import { useEffect, useState } from 'react';
import { documentApi } from '../services/documentApi';
import { useAuth } from '../contexts/AuthContext';

const POLL_INTERVAL = 2 * 60 * 1000; // 2 minutes

export function useRejectedCount() {
  const { isAuthenticated, user } = useAuth();
  const [appActive, setAppActive] = useState(AppState.currentState === 'active');

  useEffect(() => {
    const sub = AppState.addEventListener('change', (state) => {
      setAppActive(state === 'active');
    });
    return () => sub.remove();
  }, []);

  return useQuery({
    queryKey: ['rejected-count', user?.id],
    queryFn: () => documentApi.getRejectedCount().then((r) => r.data.count),
    enabled: isAuthenticated && user?.role === 'student',
    refetchInterval: appActive ? POLL_INTERVAL : false,
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: true,
    staleTime: 30 * 1000,
  });
}

export default useRejectedCount;
