import { Menu, LogOut } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

export const Header = ({ toggleSidebar }) => {
  const { user, logout } = useAuth();
  
  const roleColors = {
    student: 'bg-blue-100 text-blue-800',
    verification_staff: 'bg-yellow-100 text-yellow-800',
    admission_officer: 'bg-purple-100 text-purple-800',
    agent: 'bg-indigo-100 text-indigo-800',
    principal: 'bg-pink-100 text-pink-800',
    admin: 'bg-red-100 text-red-800',
  };

  return (
    <header className="bg-white border-b h-16 flex items-center justify-between px-4">
      <div className="flex items-center">
        <button onClick={toggleSidebar} className="md:hidden mr-4">
          <Menu className="w-6 h-6" />
        </button>
        <span className="text-xl font-bold text-primary">Admission Portal</span>
      </div>
      
      {user && (
        <div className="flex items-center space-x-4">
          <div className="flex flex-col items-end">
            <span className="text-sm font-medium text-gray-900">{user.full_name}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${roleColors[user.role] || 'bg-gray-100'}`}>
              {user.role.replace('_', ' ').toUpperCase()}
            </span>
          </div>
          <button 
            onClick={logout}
            className="text-gray-500 hover:text-danger transition-colors"
            title="Logout"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      )}
    </header>
  );
};
