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
} from 'lucide-react';
import { adminApi } from '@/api/admin';
import { KpiCard } from '@/components/KpiCard';
import { DateRangePicker } from '@/components/DateRangePicker';
import { AreaChartCard } from '@/components/charts/AreaChartCard';
import { BarChartCard } from '@/components/charts/BarChartCard';
import { MultiLineChartCard } from '@/components/charts/MultiLineChartCard';

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

  const stats = statsQuery.data;
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
            Overview of your BananaPics bot analytics and metrics.
          </p>
        </div>
        <DateRangePicker value={days} onChange={setDays} />
      </div>

      {/* Error banner */}
      {hasError && (
        <ErrorBanner message="Some data failed to load. Parts of the dashboard may be incomplete." />
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
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
          loading={isLoading}
        />
        <KpiCard
          icon={UserPlus}
          label="New Users Today"
          value={stats?.new_users_today ?? 0}
          loading={isLoading}
        />
        <KpiCard
          icon={Image}
          label="Total Generations"
          value={stats?.total_generations ?? 0}
          trend={
            stats
              ? {
                  text: `${stats.success_rate.toFixed(1)}% success`,
                  direction: stats.success_rate >= 90 ? 'up' : stats.success_rate >= 70 ? 'neutral' : 'down',
                }
              : undefined
          }
          loading={isLoading}
        />
        <KpiCard
          icon={Star}
          label="Revenue Today"
          value={stats ? `${stats.today_deposits.toLocaleString()} stars` : '0 stars'}
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
          title="Revenue Trend"
          data={revenueDailyQuery.data ?? []}
          dataKey="amount"
          color="#22C55E"
          loading={revenueDailyQuery.isLoading}
          formatValue={(v) => `${v.toLocaleString()} stars`}
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
