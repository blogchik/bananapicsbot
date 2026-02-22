import { useQuery } from '@tanstack/react-query';
import {
  Wallet,
  Activity,
  Clock,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  Zap,
  Server,
  Box,
} from 'lucide-react';
import { adminApi, type WavespeedStatus } from '@/api/admin';
import { KpiCard } from '@/components/KpiCard';
import { cn } from '@/lib/utils';

function StatusBadge({ status }: { status: WavespeedStatus['provider_status'] }) {
  const config = {
    online: { label: 'Online', dot: 'bg-success', text: 'text-success', bg: 'bg-success/10' },
    degraded: { label: 'Degraded', dot: 'bg-warning', text: 'text-warning', bg: 'bg-warning/10' },
    offline: { label: 'Offline', dot: 'bg-destructive', text: 'text-destructive', bg: 'bg-destructive/10' },
  }[status];

  return (
    <span className={cn('inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium', config.bg, config.text)}>
      <span className={cn('w-2 h-2 rounded-full', config.dot, status === 'online' && 'animate-pulse')} />
      {config.label}
    </span>
  );
}

function QueueStatusCard({
  title,
  count,
  icon: Icon,
  color,
  pulse = false,
}: {
  title: string;
  count: number;
  icon: typeof Clock;
  color: string;
  pulse?: boolean;
}) {
  return (
    <div className="bg-surface-light/30 rounded-xl p-4 flex items-center gap-3">
      <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center', color)}>
        <Icon className={cn('w-5 h-5 text-white', pulse && 'animate-pulse')} />
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{count.toLocaleString()}</p>
        <p className="text-xs text-muted-foreground">{title}</p>
      </div>
    </div>
  );
}

function StatusEmoji({ status }: { status: string }) {
  const emoji: Record<string, string> = {
    completed: 'text-success',
    failed: 'text-destructive',
    running: 'text-info',
    pending: 'text-warning',
    queued: 'text-warning',
  };
  const icons: Record<string, typeof CheckCircle2> = {
    completed: CheckCircle2,
    failed: XCircle,
    running: Loader2,
    pending: Clock,
    queued: Clock,
  };
  const Icon = icons[status] || Clock;
  return <Icon className={cn('w-4 h-4', emoji[status] || 'text-muted-foreground')} />;
}

export function WavespeedPage() {
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['admin', 'wavespeed', 'status'],
    queryFn: () => adminApi.getWavespeedStatus(),
    refetchInterval: 30_000,
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold text-white">Wavespeed Provider</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Monitor Wavespeed API status, balance, and generation analytics.
          </p>
        </div>
        <div className="flex items-center gap-3 self-start sm:self-auto">
          {data && <StatusBadge status={data.provider_status} />}
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className={cn(
              'inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all',
              'bg-surface-light/50 hover:bg-surface-light text-muted-foreground hover:text-white',
              'disabled:opacity-50',
            )}
          >
            <RefreshCw className={cn('w-4 h-4', isFetching && 'animate-spin')} />
            Refresh
          </button>
        </div>
      </div>

      {/* Error */}
      {isError && (
        <div className="flex items-center gap-3 bg-destructive-muted border border-destructive/30 text-destructive-foreground rounded-lg px-4 py-3">
          <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0" />
          <p className="text-sm">Failed to load Wavespeed data. Check API connection.</p>
        </div>
      )}

      {/* Balance & Queue */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          icon={Wallet}
          label="API Balance"
          value={data ? `$${data.balance.amount.toFixed(2)}` : '$0.00'}
          trend={
            data
              ? {
                  text: data.balance.currency,
                  direction: data.balance.amount > 10 ? 'up' : data.balance.amount > 2 ? 'neutral' : 'down',
                }
              : undefined
          }
          loading={isLoading}
        />
        <KpiCard
          icon={Clock}
          label="Queue Pending"
          value={data?.queue.pending ?? 0}
          loading={isLoading}
        />
        <KpiCard
          icon={Loader2}
          label="Queue Running"
          value={data?.queue.running ?? 0}
          loading={isLoading}
        />
        <KpiCard
          icon={Activity}
          label="Provider Status"
          value={data?.provider_status.toUpperCase() ?? 'UNKNOWN'}
          trend={
            data
              ? {
                  text: data.provider_status === 'online' ? 'All systems go' : 'Check provider',
                  direction: data.provider_status === 'online' ? 'up' : 'down',
                }
              : undefined
          }
          loading={isLoading}
        />
      </div>

      {/* 24h vs 7d Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* 24h Stats */}
        <div className="card-admin p-6">
          <div className="flex items-center gap-2 mb-4">
            <Zap className="w-5 h-5 text-banana-500" />
            <h3 className="text-lg font-semibold text-white">Last 24 Hours</h3>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <QueueStatusCard
              title="Total"
              count={data?.generations_24h.total ?? 0}
              icon={Activity}
              color="bg-banana-500/20"
            />
            <QueueStatusCard
              title="Success Rate"
              count={data?.generations_24h.success_rate ?? 0}
              icon={Zap}
              color={
                (data?.generations_24h.success_rate ?? 0) >= 90
                  ? 'bg-success/20'
                  : (data?.generations_24h.success_rate ?? 0) >= 70
                    ? 'bg-warning/20'
                    : 'bg-destructive/20'
              }
            />
            <QueueStatusCard
              title="Completed"
              count={data?.generations_24h.completed ?? 0}
              icon={CheckCircle2}
              color="bg-success/20"
            />
            <QueueStatusCard
              title="Failed"
              count={data?.generations_24h.failed ?? 0}
              icon={XCircle}
              color="bg-destructive/20"
            />
          </div>
        </div>

        {/* 7d Stats */}
        <div className="card-admin p-6">
          <div className="flex items-center gap-2 mb-4">
            <Server className="w-5 h-5 text-banana-500" />
            <h3 className="text-lg font-semibold text-white">Last 7 Days</h3>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <QueueStatusCard
              title="Total"
              count={data?.generations_7d.total ?? 0}
              icon={Activity}
              color="bg-banana-500/20"
            />
            <QueueStatusCard
              title="Success Rate"
              count={data?.generations_7d.success_rate ?? 0}
              icon={Zap}
              color={
                (data?.generations_7d.success_rate ?? 0) >= 90
                  ? 'bg-success/20'
                  : (data?.generations_7d.success_rate ?? 0) >= 70
                    ? 'bg-warning/20'
                    : 'bg-destructive/20'
              }
            />
            <QueueStatusCard
              title="Completed"
              count={data?.generations_7d.completed ?? 0}
              icon={CheckCircle2}
              color="bg-success/20"
            />
            <QueueStatusCard
              title="Failed"
              count={data?.generations_7d.failed ?? 0}
              icon={XCircle}
              color="bg-destructive/20"
            />
          </div>
        </div>
      </div>

      {/* Models Breakdown */}
      {data?.models && data.models.length > 0 && (
        <div className="card-admin p-6">
          <div className="flex items-center gap-2 mb-4">
            <Box className="w-5 h-5 text-banana-500" />
            <h3 className="text-lg font-semibold text-white">Models (24h)</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-surface-light">
                  <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider py-3 px-4">Model</th>
                  <th className="text-right text-xs font-medium text-muted-foreground uppercase tracking-wider py-3 px-4">Total</th>
                  <th className="text-right text-xs font-medium text-muted-foreground uppercase tracking-wider py-3 px-4">Completed</th>
                  <th className="text-right text-xs font-medium text-muted-foreground uppercase tracking-wider py-3 px-4">Failed</th>
                  <th className="text-right text-xs font-medium text-muted-foreground uppercase tracking-wider py-3 px-4">Success %</th>
                  <th className="text-right text-xs font-medium text-muted-foreground uppercase tracking-wider py-3 px-4">Credits</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-light/50">
                {data.models.map((m) => (
                  <tr key={m.model_key} className="hover:bg-surface-light/20 transition-colors">
                    <td className="py-3 px-4">
                      <span className="text-sm font-medium text-white">{m.model_name}</span>
                      <span className="text-xs text-muted-foreground ml-2">{m.model_key}</span>
                    </td>
                    <td className="py-3 px-4 text-right text-sm text-white">{m.total.toLocaleString()}</td>
                    <td className="py-3 px-4 text-right text-sm text-success">{m.completed.toLocaleString()}</td>
                    <td className="py-3 px-4 text-right text-sm text-destructive">{m.failed.toLocaleString()}</td>
                    <td className="py-3 px-4 text-right">
                      <span
                        className={cn(
                          'text-sm font-medium',
                          m.success_rate >= 90 ? 'text-success' : m.success_rate >= 70 ? 'text-warning' : 'text-destructive',
                        )}
                      >
                        {m.success_rate}%
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right text-sm text-muted-foreground">{m.credits.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Recent Generations */}
      {data?.recent_generations && data.recent_generations.length > 0 && (
        <div className="card-admin p-6">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-5 h-5 text-banana-500" />
            <h3 className="text-lg font-semibold text-white">Recent Generations</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-surface-light">
                  <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider py-3 px-4">Status</th>
                  <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider py-3 px-4">Model</th>
                  <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider py-3 px-4">User</th>
                  <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider py-3 px-4">Prompt</th>
                  <th className="text-right text-xs font-medium text-muted-foreground uppercase tracking-wider py-3 px-4">Cost</th>
                  <th className="text-right text-xs font-medium text-muted-foreground uppercase tracking-wider py-3 px-4">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-light/50">
                {data.recent_generations.map((gen) => (
                  <tr key={gen.id} className="hover:bg-surface-light/20 transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5">
                        <StatusEmoji status={gen.status} />
                        <span className="text-xs text-muted-foreground capitalize">{gen.status}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-sm text-white">{gen.model_name}</td>
                    <td className="py-3 px-4 text-sm text-muted-foreground font-mono">{gen.telegram_id}</td>
                    <td className="py-3 px-4 text-sm text-muted-foreground max-w-[200px] truncate">{gen.prompt || '—'}</td>
                    <td className="py-3 px-4 text-right text-sm text-white">{gen.cost ?? 0} cr</td>
                    <td className="py-3 px-4 text-right text-xs text-muted-foreground whitespace-nowrap">
                      {gen.created_at ? new Date(gen.created_at).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
