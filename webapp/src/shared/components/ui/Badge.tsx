import { type ReactNode } from 'react'
import { cn } from '@/shared/lib/cn'

interface BadgeProps {
  children: ReactNode
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'premium'
  size?: 'sm' | 'md'
  className?: string
}

export function Badge({
  children,
  variant = 'default',
  size = 'sm',
  className,
}: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center font-medium rounded-full',

        // Size
        size === 'sm' && 'px-2 py-0.5 text-xs',
        size === 'md' && 'px-3 py-1 text-sm',

        // Variants
        variant === 'default' && 'bg-white/10 text-tg-text',
        variant === 'success' && 'bg-green-500/20 text-green-500',
        variant === 'warning' && 'bg-yellow-500/20 text-yellow-500',
        variant === 'error' && 'bg-red-500/20 text-red-500',
        variant === 'info' && 'bg-blue-500/20 text-blue-500',
        variant === 'premium' && 'bg-gradient-accent text-white',

        className
      )}
    >
      {children}
    </span>
  )
}
