import { type ReactNode, type HTMLAttributes, forwardRef } from 'react'
import { cn } from '@/shared/lib/cn'

interface GlassCardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  variant?: 'default' | 'elevated' | 'outline'
  gradient?: boolean
  glow?: boolean
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

export const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  (
    {
      children,
      variant = 'default',
      gradient = false,
      glow = false,
      padding = 'md',
      className,
      ...props
    },
    ref
  ) => {
    return (
      <div
        ref={ref}
        className={cn(
          // Base glass styles
          'relative rounded-2xl overflow-hidden transition-all duration-200',
          'backdrop-blur-xl',

          // Variant styles
          variant === 'default' && [
            'bg-white/10 dark:bg-black/20',
            'border border-white/20 dark:border-white/10',
            'shadow-glass',
          ],
          variant === 'elevated' && [
            'bg-white/15 dark:bg-black/25',
            'border border-white/25 dark:border-white/15',
            'shadow-glass-lg',
          ],
          variant === 'outline' && [
            'bg-transparent',
            'border-2 border-white/20 dark:border-white/10',
          ],

          // Gradient overlay
          gradient && 'before:absolute before:inset-0 before:bg-gradient-glass before:pointer-events-none',

          // Glow effect
          glow && 'shadow-glow',

          // Padding
          padding === 'none' && 'p-0',
          padding === 'sm' && 'p-3',
          padding === 'md' && 'p-4',
          padding === 'lg' && 'p-6',

          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)

GlassCard.displayName = 'GlassCard'
