import { NavLink, useLocation } from 'react-router-dom'
import { Home, Sparkles, Images, Wrench, Wallet } from 'lucide-react'
import { cn } from '@/shared/lib/cn'
import { useHaptic } from '@/telegram/hooks'

interface NavItem {
  path: string
  label: string
  icon: React.ComponentType<{ className?: string }>
}

const navItems: NavItem[] = [
  { path: '/', label: 'Home', icon: Home },
  { path: '/generate', label: 'Generate', icon: Sparkles },
  { path: '/gallery', label: 'Gallery', icon: Images },
  { path: '/tools', label: 'Tools', icon: Wrench },
  { path: '/wallet', label: 'Wallet', icon: Wallet },
]

export function BottomNav() {
  const location = useLocation()
  const { impact } = useHaptic()

  const handleNavClick = () => {
    impact('light')
  }

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 safe-bottom">
      {/* Glass background */}
      <div className="absolute inset-0 bg-tg-bg/80 backdrop-blur-xl border-t border-white/10" />

      {/* Nav items */}
      <div className="relative flex items-center justify-around px-2 py-2">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path
          const Icon = item.icon

          return (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={handleNavClick}
              className={cn(
                'flex flex-col items-center gap-1 px-4 py-2 rounded-xl',
                'transition-all duration-200 tap-highlight',
                isActive
                  ? 'text-accent-purple'
                  : 'text-tg-hint hover:text-tg-text'
              )}
            >
              <div className="relative">
                {isActive && (
                  <div className="absolute inset-0 bg-accent-purple/20 rounded-full blur-lg scale-150" />
                )}
                <Icon
                  className={cn(
                    'relative w-6 h-6 transition-transform duration-200',
                    isActive && 'scale-110'
                  )}
                />
              </div>
              <span className="text-xs font-medium">{item.label}</span>
            </NavLink>
          )
        })}
      </div>
    </nav>
  )
}
