import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

export function AppLayout() {
  return (
    <div className="min-h-screen bg-dark-500 flex">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content area */}
      <div className="flex-1 ml-sidebar flex flex-col min-h-screen">
        {/* Topbar */}
        <Topbar />

        {/* Page content */}
        <main className="flex-1 p-6 pt-4 overflow-y-auto scrollbar-thin">
          <div className="max-w-7xl mx-auto animate-fade-in">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
