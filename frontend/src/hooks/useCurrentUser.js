import { useQuery } from '@tanstack/react-query';
import { authApi } from '../services/authApi';
import { useAuth } from '../contexts/AuthContext';

export const useCurrentUser = () => {
  const { isAuthenticated } = useAuth();
  
  return useQuery({
    queryKey: ['me'],
    queryFn: authApi.getMe,
    enabled: isAuthenticated,
  });
};
