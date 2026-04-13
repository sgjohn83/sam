import { NavLink } from 'react-router-dom';
import { ROUTES } from '../../constants/routes';
import { useAuth } from '../../contexts/AuthContext';
import { LayoutDashboard, FileText, CheckSquare, Users, BookOpen, BarChart3, Settings, Database, UserCheck } from 'lucide-react';

export const Sidebar = ({ isOpen }) => {
  const { user } = useAuth();
  if (!user) return null;

  const getNavItems = (role) => {
    const items = {
      student: [
        { label: 'Dashboard', path: ROUTES.STUDENT.DASHBOARD, icon: LayoutDashboard },
        { label: 'Application', path: ROUTES.STUDENT.APPLICATION, icon: FileText },
        { label: 'Documents', path: ROUTES.STUDENT.DOCUMENTS, icon: FileText },
        { label: 'Status', path: ROUTES.STUDENT.STATUS, icon: CheckSquare },
      ],
      verification_staff: [
        { label: 'Queue', path: ROUTES.VERIFICATION.QUEUE, icon: CheckSquare },
      ],
      admission_officer: [
        { label: 'Dashboard', path: ROUTES.OFFICER.DASHBOARD, icon: LayoutDashboard },
        { label: 'Applications', path: ROUTES.OFFICER.APPLICATIONS, icon: Users },
        { label: 'Seats', path: ROUTES.OFFICER.SEATS, icon: BookOpen },
        { label: 'Walk-in', path: ROUTES.OFFICER.WALKIN, icon: UserCheck },
      ],
      agent: [
        { label: 'Dashboard', path: ROUTES.AGENT.DASHBOARD, icon: LayoutDashboard },
        { label: 'Bulk Upload', path: ROUTES.AGENT.UPLOAD, icon: FileText },
        { label: 'Commission', path: ROUTES.AGENT.COMMISSION, icon: BarChart3 },
      ],
      principal: [
        { label: 'Dashboard', path: ROUTES.PRINCIPAL.DASHBOARD, icon: LayoutDashboard },
        { label: 'Concessions', path: ROUTES.PRINCIPAL.CONCESSIONS, icon: CheckSquare },
        { label: 'Reports', path: ROUTES.PRINCIPAL.REPORTS, icon: BarChart3 },
      ],
      admin: [
        { label: 'Dashboard', path: ROUTES.ADMIN.DASHBOARD, icon: LayoutDashboard },
        { label: 'Academic Year', path: ROUTES.ADMIN.ACADEMIC_YEAR, icon: Settings },
        { label: 'Seat Matrix', path: ROUTES.ADMIN.SEAT_MATRIX, icon: Database },
        { label: 'Fees', path: ROUTES.ADMIN.FEE_STRUCTURES, icon: BookOpen },
        { label: 'Users', path: ROUTES.ADMIN.USERS, icon: Users },
        { label: 'OCR Health', path: ROUTES.ADMIN.OCR_HEALTH, icon: BarChart3 },
        { label: 'ERP Sync', path: ROUTES.ADMIN.ERP_SYNC, icon: Database },
      ],
    };
    return items[role] || [];
  };

  return (
    <div className={`bg-white w-64 h-screen border-r flex-shrink-0 transition-all ${isOpen ? 'block' : 'hidden'} md:block`}>
      <nav className="p-4 space-y-2">
        {getNavItems(user.role).map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center p-3 rounded-lg transition-colors ${
                isActive ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-100'
              }`
            }
          >
            <item.icon className="w-5 h-5 mr-3" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
};
