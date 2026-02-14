import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Send,
  Box,
  CreditCard,
  Image,
  Settings,
  Waves,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavItem {
  label: string;
  path: string;
  icon: LucideIcon;
}

const navItems: NavItem[] = [
  { label: 'Dashboard', path: '/', icon: LayoutDashboard },
  { label: 'Users', path: '/users', icon: Users },
  { label: 'Broadcasts', path: '/broadcasts', icon: Send },
  { label: 'Models', path: '/models', icon: Box },
  { label: 'Payments', path: '/payments', icon: CreditCard },
  { label: 'Generations', path: '/generations', icon: Image },
  { label: 'Wavespeed', path: '/wavespeed', icon: Waves },
  { label: 'Settings', path: '/settings', icon: Settings },
];

export function Sidebar() {
  const location = useLocation();

  function isActive(path: string): boolean {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  }

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-sidebar bg-sidebar border-r border-sidebar-border flex flex-col z-30">
      {/* Logo */}
      <div className="h-topbar flex items-center px-6 border-b border-sidebar-border">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-accent-muted flex items-center justify-center">
            <span className="text-lg leading-none" role="img" aria-label="banana">
              🍌
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-bold text-white leading-tight">
              <span className="text-banana-500">Banana</span>Pics
            </span>
            <span className="text-[10px] font-medium text-muted uppercase tracking-widest leading-tight">
              Admin
            </span>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto scrollbar-hide">
        <div className="mb-3 px-3">
          <span className="text-[10px] font-semibold text-muted uppercase tracking-widest">
            Menu
          </span>
        </div>
        {navItems.map((item) => {
          const active = isActive(item.path);
          const Icon = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group relative',
                active
                  ? 'text-banana-500 bg-accent-muted'
                  : 'text-muted-foreground hover:text-white hover:bg-sidebar-hover',
              )}
            >
              {/* Active indicator bar */}
              {active && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-banana-500 rounded-r-full" />
              )}

              <Icon
                className={cn(
                  'w-[18px] h-[18px] flex-shrink-0 transition-colors duration-150',
                  active ? 'text-banana-500' : 'text-muted group-hover:text-white',
                )}
              />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom section */}
      <div className="px-4 py-4 border-t border-sidebar-border">
        <div className="flex items-center gap-2 px-2">
          <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
          <span className="text-xs text-muted-foreground">System Online</span>
        </div>
      </div>
    </aside>
  );
}
