import { NavLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { 
  LayoutDashboard, 
  Users, 
  UserPlus, 
  BarChart3, 
  UserCircle, 
  CheckCircle,
  Clock
} from 'lucide-react';

export function AgentSidebar({ isOpen }) {
  const { user } = useAuth();
  
  if (!user || user.role !== 'agent') return null;

  // Assuming agent_data is injected into user object via backend update
  const agent = user.agent_data || { agency_name: 'Agency Name', is_verified: false };

  const navItems = [
    { label: 'Dashboard', path: '/agent/dashboard', icon: LayoutDashboard },
    { label: 'My Students', path: '/agent/students', icon: Users },
    { label: 'Register Student', path: '/agent/students/register', icon: UserPlus },
    { label: 'Commissions', path: '/agent/commissions', icon: BarChart3 },
    { label: 'Profile', path: '/agent/profile', icon: UserCircle },
  ];

  return (
    <div className={`bg-white w-64 h-screen border-r flex-shrink-0 flex flex-col transition-all ${isOpen ? 'block' : 'hidden'} md:block`}>
      {/* Agent Info Header */}
      <div className="p-6 border-bottom bg-gray-50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-lg">
            {agent.agency_name?.charAt(0) || 'A'}
          </div>
          <div className="overflow-hidden">
            <h3 className="font-semibold text-gray-900 truncate" title={agent.agency_name}>
              {agent.agency_name}
            </h3>
            <div className="flex items-center gap-1.5 mt-0.5">
              {agent.is_verified ? (
                <>
                  <CheckCircle className="w-3.5 h-3.5 text-green-600" />
                  <span className="text-xs font-medium text-green-700">Verified</span>
                </>
              ) : (
                <>
                  <Clock className="w-3.5 h-3.5 text-amber-500" />
                  <span className="text-xs font-medium text-amber-600">Pending</span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      <nav className="p-4 space-y-1.5 flex-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center p-3 rounded-lg transition-all duration-200 group ${
                isActive 
                  ? 'bg-blue-50 text-blue-700 shadow-sm border-blue-100 ring-1 ring-blue-100' 
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              }`
            }
          >
            <item.icon className="w-5 h-5 mr-3 transition-transform group-hover:scale-110" />
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t text-center">
        <p className="text-[10px] text-gray-400 uppercase tracking-widest font-bold">
          Agent Management v1.0
        </p>
      </div>
    </div>
  );
}
