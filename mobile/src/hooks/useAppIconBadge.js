import { useEffect } from 'react';
import * as Notifications from 'expo-notifications';
import { useRejectedCount } from './useRejectedCount';

export function useAppIconBadge() {
  const { data: count = 0 } = useRejectedCount();

  useEffect(() => {
    Notifications.setBadgeCountAsync(count).catch(() => {});
  }, [count]);
}

export default useAppIconBadge;