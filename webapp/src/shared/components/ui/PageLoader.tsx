import { cn } from '@/shared/lib/cn'

interface PageLoaderProps {
  className?: string
  text?: string
}

export function PageLoader({ className, text }: PageLoaderProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center min-h-[50vh] gap-4', className)}>
      <div className="relative">
        {/* Outer glow */}
        <div className="absolute inset-0 bg-gradient-accent rounded-full blur-xl opacity-30 animate-pulse-slow" />

        {/* Spinner */}
        <div className="relative w-12 h-12 border-3 border-white/10 border-t-accent-purple rounded-full animate-spin" />
      </div>

      {text && (
        <p className="text-sm text-tg-hint animate-pulse">{text}</p>
      )}
    </div>
  )
}

export function InlineLoader({ className }: { className?: string }) {
  return (
    <div className={cn('flex items-center justify-center py-8', className)}>
      <div className="w-6 h-6 border-2 border-white/10 border-t-accent-purple rounded-full animate-spin" />
    </div>
  )
}
