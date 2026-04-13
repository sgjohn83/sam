import { ROUTES } from '../constants/routes';

export const getHomeRoute = (role) => {
  const roleMap = {
    student: ROUTES.STUDENT.DASHBOARD,
    verification_staff: ROUTES.VERIFICATION.QUEUE,
    admission_officer: ROUTES.OFFICER.DASHBOARD,
    agent: ROUTES.AGENT.DASHBOARD,
    principal: ROUTES.PRINCIPAL.DASHBOARD,
    admin: ROUTES.ADMIN.DASHBOARD,
  };
  return roleMap[role] || '/';
};
