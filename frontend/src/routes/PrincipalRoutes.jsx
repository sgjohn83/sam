import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export function PrincipalRoutes() {
  const { user } = useAuth();
  if (!['principal', 'admin'].includes(user?.role)) {
    return <Navigate to="/dashboard" replace />;
  }
  return <Outlet />;
}

