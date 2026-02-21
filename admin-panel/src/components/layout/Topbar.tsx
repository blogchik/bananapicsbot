import { useLocation, useNavigate } from 'react-router-dom';
import { LogOut, Menu, User } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { clearToken } from '@/api/client';

const pageTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/users': 'Users',
  '/broadcasts': 'Broadcasts',
  '/broadcasts/new': 'New Broadcast',
  '/models': 'Models',
  '/payments': 'Payments',
  '/generations': 'Generations',
  '/settings': 'Settings',
};

function getPageTitle(pathname: string): string {
  // Check exact match first
  if (pageTitles[pathname]) return pageTitles[pathname];

  // Check for dynamic routes like /users/:id
  if (pathname.startsWith('/users/')) return 'User Detail';

  // Fallback: capitalize the first path segment
  const segment = pathname.split('/')[1];
  if (segment) return segment.charAt(0).toUpperCase() + segment.slice(1);

  return 'Dashboard';
}

interface TopbarProps {
  onMenuClick?: () => void;
}

export function Topbar({ onMenuClick }: TopbarProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { admin, logout } = useAuthStore();

  const title = getPageTitle(location.pathname);

  const handleLogout = () => {
    clearToken();
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <header className="h-topbar bg-dark-500/80 backdrop-blur-md border-b border-surface-lighter/30 flex items-center justify-between px-4 lg:px-6 sticky top-0 z-20">
      {/* Left: hamburger (mobile) + page title */}
      <div className="flex items-center gap-3">
        {/* Hamburger button — mobile only */}
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded-lg text-muted-foreground hover:text-white hover:bg-surface-light transition-colors"
          aria-label="Toggle menu"
        >
          <Menu className="w-5 h-5" />
        </button>
        <h1 className="text-lg font-semibold text-white">{title}</h1>
      </div>

      {/* Right section */}
      <div className="flex items-center gap-4">
        {/* Admin info */}
        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-medium text-white leading-tight">
              {admin?.first_name || 'Admin'}
            </p>
            {admin?.username && (
              <p className="text-xs text-muted leading-tight">@{admin.username}</p>
            )}
          </div>

          {/* Avatar */}
          <div className="w-8 h-8 rounded-lg bg-surface-light flex items-center justify-center">
            <User className="w-4 h-4 text-muted-foreground" />
          </div>
        </div>

        {/* Divider */}
        <div className="w-px h-6 bg-surface-lighter/50" />

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive-muted transition-colors duration-150 text-sm"
          title="Sign out"
        >
          <LogOut className="w-4 h-4" />
          <span className="hidden sm:inline">Sign out</span>
        </button>
      </div>
    </header>
  );
}
