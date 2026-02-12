import { type LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';
import { cn } from '@/lib/utils';

interface KpiCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  trend?: {
    text: string;
    direction: 'up' | 'down' | 'neutral';
  };
  loading?: boolean;
}

function formatValue(value: string | number): string {
  if (typeof value === 'number') {
    return value.toLocaleString('en-US');
  }
  return value;
}

export function KpiCard({ icon: Icon, label, value, trend, loading }: KpiCardProps) {
  if (loading) {
    return (
      <div className="card-admin p-5 group">
        <div className="flex items-start justify-between">
          <div className="space-y-2 flex-1">
            <div className="h-4 w-24 bg-surface-light rounded animate-pulse-soft" />
            <div className="h-8 w-20 bg-surface-light rounded animate-pulse-soft" />
            <div className="h-3 w-28 bg-surface-light rounded animate-pulse-soft" />
          </div>
          <div className="w-10 h-10 rounded-lg bg-surface-light animate-pulse-soft" />
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        'card-admin p-5 group transition-all duration-200',
        'hover:shadow-glow-sm hover:border-banana-500/20',
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-muted-foreground mb-1">{label}</p>
          <p className="text-2xl font-bold text-white tracking-tight">
            {formatValue(value)}
          </p>
          {trend && (
            <div className="flex items-center gap-1 mt-1.5">
              {trend.direction === 'up' && (
                <TrendingUp className="w-3 h-3 text-success" />
              )}
              {trend.direction === 'down' && (
                <TrendingDown className="w-3 h-3 text-destructive" />
              )}
              <span
                className={cn(
                  'text-xs font-medium',
                  trend.direction === 'up' && 'text-success',
                  trend.direction === 'down' && 'text-destructive',
                  trend.direction === 'neutral' && 'text-muted-foreground',
                )}
              >
                {trend.text}
              </span>
            </div>
          )}
        </div>
        <div className="w-10 h-10 rounded-lg bg-accent-muted flex items-center justify-center transition-colors duration-200 group-hover:bg-banana-500/20">
          <Icon className="w-5 h-5 text-banana-500" />
        </div>
      </div>
    </div>
  );
}
