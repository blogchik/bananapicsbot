import { type TextareaHTMLAttributes, forwardRef } from 'react'
import { cn } from '@/shared/lib/cn'

interface GlassTextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  helperText?: string
}

export const GlassTextarea = forwardRef<HTMLTextAreaElement, GlassTextareaProps>(
  ({ label, error, helperText, className, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-tg-text mb-2">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          className={cn(
            // Base styles
            'w-full px-4 py-3 rounded-xl resize-none',
            'bg-white/10 dark:bg-black/20',
            'backdrop-blur-md',
            'border border-white/20 dark:border-white/10',
            'text-tg-text placeholder:text-tg-hint/60',
            'transition-all duration-200',

            // Focus styles
            'focus:outline-none focus:ring-2 focus:ring-accent-purple/50',
            'focus:border-accent-purple/50',

            // Error styles
            error && 'border-red-500/50 focus:ring-red-500/50 focus:border-red-500/50',

            // Scrollbar
            'no-scrollbar',

            className
          )}
          {...props}
        />
        {error && (
          <p className="mt-1.5 text-sm text-red-500">{error}</p>
        )}
        {helperText && !error && (
          <p className="mt-1.5 text-sm text-tg-hint">{helperText}</p>
        )}
      </div>
    )
  }
)

GlassTextarea.displayName = 'GlassTextarea'
