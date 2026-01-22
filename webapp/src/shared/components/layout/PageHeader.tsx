import { type ReactNode } from 'react'
import { cn } from '@/shared/lib/cn'
import { useBackButton } from '@/telegram/hooks'

interface PageHeaderProps {
  title: string
  subtitle?: string
  showBack?: boolean
  action?: ReactNode
  className?: string
}

export function PageHeader({
  title,
  subtitle,
  showBack = false,
  action,
  className,
}: PageHeaderProps) {
  // Manage Telegram back button
  useBackButton(showBack)

  return (
    <header className={cn('px-4 pt-4 pb-2', className)}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-tg-text">{title}</h1>
          {subtitle && (
            <p className="mt-1 text-sm text-tg-hint">{subtitle}</p>
          )}
        </div>
        {action && <div className="flex-shrink-0">{action}</div>}
      </div>
    </header>
  )
}
