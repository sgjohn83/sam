import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ROUTES } from '../constants/routes';

export const GuestRoute = () => {
  const { isAuthenticated, user, isLoading } = useAuth();

  if (isLoading) {
    return <div className="flex h-screen items-center justify-center">Loading...</div>;
  }

  if (isAuthenticated) {
    // Redirect based on role
    const homePaths = {
      student: ROUTES.STUDENT.DASHBOARD,
      verification_staff: ROUTES.VERIFICATION.QUEUE,
      admission_officer: ROUTES.OFFICER.DASHBOARD,
      agent: ROUTES.AGENT.DASHBOARD,
      principal: ROUTES.PRINCIPAL.DASHBOARD,
      admin: ROUTES.ADMIN.DASHBOARD,
    };
    return <Navigate to={homePaths[user.role] || '/'} replace />;
  }

  return <Outlet />;
};
