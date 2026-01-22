import { cn } from '@/shared/lib/cn'

interface SkeletonProps {
  className?: string
  variant?: 'default' | 'circular' | 'text'
  width?: string | number
  height?: string | number
}

export function Skeleton({
  className,
  variant = 'default',
  width,
  height,
}: SkeletonProps) {
  return (
    <div
      className={cn(
        'animate-pulse bg-white/10 dark:bg-white/5',
        variant === 'default' && 'rounded-xl',
        variant === 'circular' && 'rounded-full',
        variant === 'text' && 'rounded-md h-4',
        className
      )}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height,
      }}
    />
  )
}

// Common skeleton compositions
export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn('glass-card space-y-3', className)}>
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-8 w-full" />
      <Skeleton className="h-4 w-2/3" />
    </div>
  )
}

export function SkeletonAvatar({ size = 40 }: { size?: number }) {
  return <Skeleton variant="circular" width={size} height={size} />
}

export function SkeletonText({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          variant="text"
          className={i === lines - 1 ? 'w-2/3' : 'w-full'}
        />
      ))}
    </div>
  )
}
