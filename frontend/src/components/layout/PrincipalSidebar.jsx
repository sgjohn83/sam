import { NavLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
  LayoutDashboard,
  Grid3X3,
  IndianRupee,
  Users,
  ShieldCheck,
  ClipboardList,
} from 'lucide-react';

function getAcademicYearLabel() {
  const now = new Date();
  const year = now.getFullYear();
  const nextYear = year + 1;
  return `${year}-${String(nextYear).slice(-2)}`;
}

export function PrincipalSidebar({ isOpen, academicYearLabel }) {
  const { user } = useAuth();
  if (!user || !['principal', 'admin'].includes(user.role)) return null;

  const navItems = [
    { label: 'Dashboard', path: '/principal/dashboard', icon: LayoutDashboard },
    { label: 'Seat Matrix', path: '/principal/seats', icon: Grid3X3 },
    { label: 'Revenue', path: '/principal/revenue', icon: IndianRupee },
    { label: 'Agent Performance', path: '/principal/agents', icon: Users },
    { label: 'Verification', path: '/principal/verification', icon: ShieldCheck },
    { label: 'Audit Trail', path: '/principal/audit-trail', icon: ClipboardList },
  ];

  const principalName = user.full_name || user.name || user.email || 'Principal';
  const yearLabel = academicYearLabel || getAcademicYearLabel();

  return (
    <div className={`bg-white w-64 h-screen border-r flex-shrink-0 flex flex-col transition-all ${isOpen ? 'block' : 'hidden'} md:block`}>
      <div className="p-6 border-b bg-gray-50">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Academic Year</p>
        <h2 className="mt-1 text-lg font-bold text-gray-900">{yearLabel}</h2>
        <p className="mt-2 text-sm text-gray-700 truncate" title={principalName}>{principalName}</p>
      </div>

      <nav className="p-4 space-y-1.5 flex-1">
        {navItems.map((item) => (
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
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}

