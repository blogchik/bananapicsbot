import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Star,
  CreditCard,
  Receipt,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { cn } from '@/lib/utils';
import { KpiCard } from '@/components/KpiCard';
import { AreaChartCard } from '@/components/charts/AreaChartCard';
import { paymentsApi } from '@/api/payments';

const PAGE_SIZE = 50;

const DATE_PRESETS = [
  { label: '7d', value: 7 },
  { label: '30d', value: 30 },
  { label: '90d', value: 90 },
];

// --- Pagination ---

function Pagination({
  page,
  totalPages,
  onPageChange,
}: {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between px-4 py-3">
      <p className="text-sm text-muted-foreground">
        Page {page + 1} of {totalPages}
      </p>
      <div className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page === 0}
          className={cn(
            'p-1.5 rounded-lg transition-colors',
            page === 0
              ? 'text-muted cursor-not-allowed'
              : 'text-muted-foreground hover:bg-surface-light hover:text-white',
          )}
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        {Array.from({ length: Math.min(totalPages, 5) }).map((_, i) => {
          let pageNum: number;
          if (totalPages <= 5) {
            pageNum = i;
          } else if (page < 3) {
            pageNum = i;
          } else if (page > totalPages - 4) {
            pageNum = totalPages - 5 + i;
          } else {
            pageNum = page - 2 + i;
          }
          return (
            <button
              key={pageNum}
              onClick={() => onPageChange(pageNum)}
              className={cn(
                'w-8 h-8 rounded-lg text-sm font-medium transition-colors',
                pageNum === page
                  ? 'bg-banana-500 text-dark-500'
                  : 'text-muted-foreground hover:bg-surface-light hover:text-white',
              )}
            >
              {pageNum + 1}
            </button>
          );
        })}
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages - 1}
          className={cn(
            'p-1.5 rounded-lg transition-colors',
            page >= totalPages - 1
              ? 'text-muted cursor-not-allowed'
              : 'text-muted-foreground hover:bg-surface-light hover:text-white',
          )}
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// --- Refund Badge ---

function RefundBadge({ refunded }: { refunded: boolean }) {
  if (!refunded) return <span className="text-sm text-muted-foreground">--</span>;
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-destructive/15 text-destructive border border-destructive/25">
      Refunded
    </span>
  );
}

// --- Table Skeleton ---

function TableSkeleton() {
  return (
    <>
      {Array.from({ length: 8 }).map((_, i) => (
        <tr key={i} className="border-b border-surface-lighter/30">
          {Array.from({ length: 6 }).map((_, j) => (
            <td key={j} className="px-4 py-3">
              <div className="h-4 w-16 bg-surface-light rounded animate-pulse-soft" />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

// --- Main Page ---

export function PaymentsPage() {
  const [page, setPage] = useState(0);
  const [chartDays, setChartDays] = useState(30);

  const paymentsQuery = useQuery({
    queryKey: ['admin', 'payments', page],
    queryFn: () => paymentsApi.getPayments(page * PAGE_SIZE, PAGE_SIZE),
  });

  const dailyQuery = useQuery({
    queryKey: ['admin', 'payments-daily', chartDays],
    queryFn: () => paymentsApi.getPaymentsDaily(chartDays),
    refetchInterval: 60_000,
  });

  const payments = paymentsQuery.data?.items ?? [];
  const total = paymentsQuery.data?.total ?? 0;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  // Compute KPI values from full list (approximate from what we have)
  const kpiStats = useMemo(() => {
    const allPayments = payments;
    const totalStars = allPayments.reduce((sum, p) => sum + p.stars_amount, 0);
    const avgPayment = allPayments.length > 0 ? totalStars / allPayments.length : 0;
    return {
      totalStars,
      totalCount: total,
      avgPayment: Math.round(avgPayment),
    };
  }, [payments, total]);

  const isLoading = paymentsQuery.isLoading;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white">Payments</h2>
        <p className="text-sm text-muted-foreground mt-1">
          View payment transactions, revenue, and billing history.
        </p>
      </div>

      {/* Error banner */}
      {paymentsQuery.isError && (
        <div className="flex items-center gap-3 bg-destructive-muted border border-destructive/30 text-destructive-foreground rounded-lg px-4 py-3">
          <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0" />
          <p className="text-sm">Failed to load payments data. Please try again.</p>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <KpiCard
          icon={Star}
          label="Total Stars (page)"
          value={kpiStats.totalStars}
          loading={isLoading}
        />
        <KpiCard
          icon={Receipt}
          label="Total Payments"
          value={kpiStats.totalCount}
          loading={isLoading}
        />
        <KpiCard
          icon={CreditCard}
          label="Avg Payment (page)"
          value={`${kpiStats.avgPayment} stars`}
          loading={isLoading}
        />
      </div>

      {/* Payments Table */}
      <div className="card-admin overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-surface-lighter/50">
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  User ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Stars
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Credits
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Provider
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Refunded
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Date
                </th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <TableSkeleton />
              ) : payments.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center">
                    <div className="flex flex-col items-center">
                      <div className="w-12 h-12 rounded-xl bg-accent-muted flex items-center justify-center mb-3">
                        <CreditCard className="w-6 h-6 text-banana-500" />
                      </div>
                      <p className="text-sm text-muted-foreground">
                        No payments found
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                payments.map((payment) => (
                  <tr
                    key={payment.id}
                    className="border-b border-surface-lighter/30 hover:bg-surface-light/30 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <span className="text-sm font-mono text-white">
                        {payment.user_id}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm font-medium text-banana-400">
                        {payment.stars_amount.toLocaleString()}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-white">
                        {payment.credits_amount.toLocaleString()}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-muted-foreground capitalize">
                        {payment.provider}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <RefundBadge refunded={payment.is_refunded} />
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-muted-foreground">
                        {formatDate(payment.created_at)}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
      </div>

      {/* Revenue Chart */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-white">Payment Revenue</h3>
          <div className="flex items-center gap-1">
            {DATE_PRESETS.map((preset) => (
              <button
                key={preset.value}
                onClick={() => setChartDays(preset.value)}
                className={cn(
                  'px-3 py-1 rounded-lg text-xs font-medium transition-colors',
                  chartDays === preset.value
                    ? 'bg-banana-500 text-dark-500'
                    : 'text-muted-foreground hover:bg-surface-light hover:text-white',
                )}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>
        <AreaChartCard
          title=""
          data={dailyQuery.data ?? []}
          dataKey="amount"
          color="#22C55E"
          loading={dailyQuery.isLoading}
          formatValue={(v) => `${v.toLocaleString()} stars`}
        />
      </div>
    </div>
  );
}

// --- Helpers ---

function formatDate(dateStr: string): string {
  try {
    return format(parseISO(dateStr), 'MMM d, yyyy HH:mm');
  } catch {
    return dateStr;
  }
}
