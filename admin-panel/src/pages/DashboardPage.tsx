import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Users,
  Activity,
  UserPlus,
  Image,
  Star,
  CreditCard,
  AlertCircle,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  Ban,
  TrendingUp,
  Zap,
  Server,
  BarChart3,
} from 'lucide-react';
import { adminApi } from '@/api/admin';
import { generationsApi } from '@/api/generations';
import { KpiCard } from '@/components/KpiCard';
import { DateRangePicker } from '@/components/DateRangePicker';
import { AreaChartCard } from '@/components/charts/AreaChartCard';
import { BarChartCard } from '@/components/charts/BarChartCard';
import { MultiLineChartCard } from '@/components/charts/MultiLineChartCard';
import { cn } from '@/lib/utils';

const GENERATION_LINES = [
  { dataKey: 'total', label: 'Total', color: '#E6B800' },
  { dataKey: 'completed', label: 'Completed', color: '#22C55E' },
  { dataKey: 'failed', label: 'Failed', color: '#EF4444' },
];

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-3 bg-destructive-muted border border-destructive/30 text-destructive-foreground rounded-lg px-4 py-3">
      <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0" />
      <p className="text-sm">{message}</p>
    </div>
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

export function DashboardPage() {
  const [days, setDays] = useState(30);

  // --- Data fetching ---

  const statsQuery = useQuery({
    queryKey: ['admin', 'stats', days],
    queryFn: () => adminApi.getStats(days),
    refetchInterval: 60_000,
  });

  const usersDailyQuery = useQuery({
    queryKey: ['admin', 'users-daily', days],
    queryFn: () => adminApi.getUsersDaily(days),
    refetchInterval: 60_000,
  });

  const generationsDailyQuery = useQuery({
    queryKey: ['admin', 'generations-daily', days],
    queryFn: () => adminApi.getGenerationsDaily(days),
    refetchInterval: 60_000,
  });

  const revenueDailyQuery = useQuery({
    queryKey: ['admin', 'revenue-daily', days],
    queryFn: () => adminApi.getRevenueDaily(days),
    refetchInterval: 60_000,
  });

  const modelsBreakdownQuery = useQuery({
    queryKey: ['admin', 'models-breakdown'],
    queryFn: () => adminApi.getModelsBreakdown(),
    refetchInterval: 60_000,
  });

  // Queue status - real-time monitoring
  const queueQuery = useQuery({
    queryKey: ['admin', 'generations', 'queue'],
    queryFn: () => generationsApi.getQueueStatus(),
    refetchInterval: 10_000, // More frequent for real-time
  });

  const stats = statsQuery.data;
  const queue = queueQuery.data;
  const isLoading = statsQuery.isLoading;
  const hasError =
    statsQuery.isError ||
    usersDailyQuery.isError ||
    generationsDailyQuery.isError ||
    revenueDailyQuery.isError ||
    modelsBreakdownQuery.isError;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Dashboard</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Real-time overview of BananaPics bot analytics and system status.
          </p>
        </div>
        <DateRangePicker value={days} onChange={setDays} />
      </div>

      {/* Error banner */}
      {hasError && (
        <ErrorBanner message="Some data failed to load. Parts of the dashboard may be incomplete." />
      )}

      {/* Real-time Queue Monitor */}
      <div className="card-admin p-6">
        <div className="flex items-center gap-2 mb-4">
          <Server className="w-5 h-5 text-banana-500" />
          <h3 className="text-lg font-semibold text-white">Generation Queue Monitor</h3>
          <span className="ml-auto flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
            Live
          </span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <QueueStatusCard
            title="Queued"
            count={queue?.queued ?? 0}
            icon={Clock}
            color="bg-warning/20"
          />
          <QueueStatusCard
            title="Running"
            count={queue?.running ?? 0}
            icon={Loader2}
            color="bg-info/20"
            pulse
          />
          <QueueStatusCard
            title="Completed"
            count={queue?.completed ?? 0}
            icon={CheckCircle2}
            color="bg-success/20"
          />
          <QueueStatusCard
            title="Failed"
            count={queue?.failed ?? 0}
            icon={XCircle}
            color="bg-destructive/20"
          />
        </div>
      </div>

      {/* KPI Cards - Users & Activity */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          icon={Users}
          label="Total Users"
          value={stats?.total_users ?? 0}
          trend={
            stats
              ? {
                  text: `+${stats.new_users_today.toLocaleString()} today`,
                  direction: stats.new_users_today > 0 ? 'up' : 'neutral',
                }
              : undefined
          }
          loading={isLoading}
        />
        <KpiCard
          icon={Activity}
          label="Active Users (7d)"
          value={stats?.active_users_7d ?? 0}
          trend={
            stats
              ? {
                  text: `${stats.active_users_30d?.toLocaleString() ?? 0} (30d)`,
                  direction: 'neutral',
                }
              : undefined
          }
          loading={isLoading}
        />
        <KpiCard
          icon={UserPlus}
          label="New This Week"
          value={stats?.new_users_week ?? 0}
          trend={
            stats
              ? {
                  text: `${stats.new_users_month?.toLocaleString() ?? 0} this month`,
                  direction: 'neutral',
                }
              : undefined
          }
          loading={isLoading}
        />
        <KpiCard
          icon={Ban}
          label="Banned Users"
          value={stats?.banned_users ?? 0}
          loading={isLoading}
        />
      </div>

      {/* KPI Cards - Generations & Performance */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          icon={Image}
          label="Total Generations"
          value={stats?.total_generations ?? 0}
          loading={isLoading}
        />
        <KpiCard
          icon={Zap}
          label="Success Rate"
          value={stats ? `${stats.success_rate.toFixed(1)}%` : '0%'}
          trend={
            stats
              ? {
                  text: stats.success_rate >= 90 ? 'Excellent' : stats.success_rate >= 70 ? 'Good' : 'Needs attention',
                  direction: stats.success_rate >= 90 ? 'up' : stats.success_rate >= 70 ? 'neutral' : 'down',
                }
              : undefined
          }
          loading={isLoading}
        />
        <KpiCard
          icon={BarChart3}
          label="Avg. Gen Time"
          value={stats?.avg_generation_time ? `${stats.avg_generation_time.toFixed(1)}s` : 'N/A'}
          loading={isLoading}
        />
        <KpiCard
          icon={TrendingUp}
          label="Today's Generations"
          value={stats?.today_generations ?? 0}
          loading={isLoading}
        />
      </div>

      {/* KPI Cards - Revenue & Payments */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          icon={Star}
          label="Total Revenue"
          value={stats ? `${(stats.total_deposits ?? 0).toLocaleString()} ⭐` : '0 ⭐'}
          loading={isLoading}
        />
        <KpiCard
          icon={Star}
          label="Revenue Today"
          value={stats ? `${stats.today_deposits.toLocaleString()} ⭐` : '0 ⭐'}
          loading={isLoading}
        />
        <KpiCard
          icon={CreditCard}
          label="Completed Payments"
          value={stats?.completed_payments ?? 0}
          trend={
            stats
              ? {
                  text: `${stats.payment_success_rate.toFixed(1)}% success`,
                  direction: stats.payment_success_rate >= 90 ? 'up' : stats.payment_success_rate >= 70 ? 'neutral' : 'down',
                }
              : undefined
          }
          loading={isLoading}
        />
        <KpiCard
          icon={TrendingUp}
          label="Credits Spent"
          value={stats ? `${(stats.total_spent ?? 0).toLocaleString()}` : '0'}
          loading={isLoading}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* User Growth */}
        <AreaChartCard
          title="User Growth"
          data={usersDailyQuery.data ?? []}
          dataKey="count"
          loading={usersDailyQuery.isLoading}
        />

        {/* Generation Volume */}
        <MultiLineChartCard
          title="Generation Volume"
          data={generationsDailyQuery.data ?? []}
          lines={GENERATION_LINES}
          loading={generationsDailyQuery.isLoading}
        />

        {/* Revenue Trend */}
        <AreaChartCard
          title="Revenue Trend (Stars)"
          data={revenueDailyQuery.data ?? []}
          dataKey="amount"
          color="#22C55E"
          loading={revenueDailyQuery.isLoading}
          formatValue={(v) => `${v.toLocaleString()} ⭐`}
        />

        {/* Generations by Model */}
        <BarChartCard
          title="Generations by Model"
          data={modelsBreakdownQuery.data ?? []}
          dataKey="count"
          nameKey="model_name"
          layout="horizontal"
          loading={modelsBreakdownQuery.isLoading}
        />
      </div>
    </div>
  );
}
