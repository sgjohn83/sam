import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export const MainLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen bg-gray-50">
      <div className={`fixed inset-0 z-20 md:relative md:inset-auto ${sidebarOpen ? 'block' : 'hidden'} md:block`}>
        <div className="md:hidden absolute inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        <Sidebar isOpen={true} />
      </div>
      
      <div className="flex flex-col flex-1 w-full overflow-hidden">
        <Header toggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
