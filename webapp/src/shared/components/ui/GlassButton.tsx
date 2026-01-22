import { type ButtonHTMLAttributes, forwardRef } from 'react'
import { cn } from '@/shared/lib/cn'
import { useHaptic } from '@/telegram/hooks'

interface GlassButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'ghost' | 'destructive'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  fullWidth?: boolean
  haptic?: boolean
}

export const GlassButton = forwardRef<HTMLButtonElement, GlassButtonProps>(
  (
    {
      children,
      variant = 'default',
      size = 'md',
      loading = false,
      fullWidth = false,
      haptic: enableHaptic = true,
      className,
      disabled,
      onClick,
      ...props
    },
    ref
  ) => {
    const { impact } = useHaptic()

    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      if (enableHaptic && !disabled && !loading) {
        impact('light')
      }
      onClick?.(e)
    }

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        onClick={handleClick}
        className={cn(
          // Base styles
          'relative inline-flex items-center justify-center gap-2',
          'font-medium rounded-xl transition-all duration-200',
          'active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none',
          'backdrop-blur-md',

          // Size variants
          size === 'sm' && 'px-3 py-2 text-sm',
          size === 'md' && 'px-4 py-3 text-base',
          size === 'lg' && 'px-6 py-4 text-lg',

          // Style variants
          variant === 'default' && [
            'bg-white/10 dark:bg-white/5',
            'border border-white/20 dark:border-white/10',
            'hover:bg-white/15 dark:hover:bg-white/10',
            'text-tg-text',
          ],
          variant === 'primary' && [
            'bg-gradient-accent',
            'border-0',
            'text-white',
            'shadow-glow hover:shadow-lg',
          ],
          variant === 'secondary' && [
            'bg-tg-button/20',
            'border border-tg-button/30',
            'text-tg-button',
            'hover:bg-tg-button/30',
          ],
          variant === 'ghost' && [
            'bg-transparent',
            'border-0',
            'hover:bg-white/10 dark:hover:bg-white/5',
            'text-tg-text',
          ],
          variant === 'destructive' && [
            'bg-red-500/20',
            'border border-red-500/30',
            'text-red-500',
            'hover:bg-red-500/30',
          ],

          // Full width
          fullWidth && 'w-full',

          className
        )}
        {...props}
      >
        {loading ? (
          <>
            <div className="w-4 h-4 border-2 border-current/30 border-t-current rounded-full animate-spin" />
            <span className="opacity-70">{children}</span>
          </>
        ) : (
          children
        )}
      </button>
    )
  }
)

GlassButton.displayName = 'GlassButton'
