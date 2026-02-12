import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  Clock,
  Play,
  Layers,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Image,
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { cn } from '@/lib/utils';
import { KpiCard } from '@/components/KpiCard';
import { generationsApi, type AdminGeneration } from '@/api/generations';

const PAGE_SIZE = 50;

const STATUS_TABS = [
  { label: 'All', value: '' },
  { label: 'Completed', value: 'completed' },
  { label: 'Failed', value: 'failed' },
  { label: 'Running', value: 'running' },
  { label: 'Queued', value: 'queued' },
];

// --- Status Badge ---

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { className: string; pulse?: boolean }> = {
    completed: { className: 'bg-success/15 text-success border-success/25' },
    failed: { className: 'bg-destructive/15 text-destructive border-destructive/25' },
    running: { className: 'bg-info/15 text-info border-info/25', pulse: true },
    queued: { className: 'bg-warning/15 text-warning border-warning/25' },
    pending: { className: 'bg-surface-light text-muted-foreground border-surface-lighter/50' },
  };

  const cfg = config[status] ?? config.pending;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-semibold border capitalize',
        cfg.className,
      )}
    >
      {cfg.pulse && (
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-info opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-info" />
        </span>
      )}
      {status}
    </span>
  );
}

// --- Expandable Prompt Row ---

function GenerationRow({ gen }: { gen: AdminGeneration }) {
  const [expanded, setExpanded] = useState(false);
  const maxLength = 60;
  const isLongPrompt = gen.prompt.length > maxLength;
  const displayPrompt = expanded || !isLongPrompt
    ? gen.prompt
    : gen.prompt.slice(0, maxLength) + '...';

  return (
    <>
      <tr className="border-b border-surface-lighter/30 hover:bg-surface-light/30 transition-colors">
        <td className="px-4 py-3">
          <span className="text-sm font-mono text-white">
            {gen.user_telegram_id}
          </span>
        </td>
        <td className="px-4 py-3">
          <div>
            <p className="text-sm text-white">{gen.model_name}</p>
            <p className="text-xs text-muted-foreground font-mono">{gen.model_key}</p>
          </div>
        </td>
        <td className="px-4 py-3 max-w-xs">
          <button
            onClick={() => isLongPrompt && setExpanded(!expanded)}
            className={cn(
              'text-sm text-left',
              isLongPrompt ? 'text-white hover:text-banana-400 cursor-pointer' : 'text-white cursor-default',
            )}
          >
            <span>{displayPrompt}</span>
            {isLongPrompt && (
              <span className="inline-flex ml-1 align-middle">
                {expanded ? (
                  <ChevronUp className="w-3 h-3 text-muted-foreground" />
                ) : (
                  <ChevronDown className="w-3 h-3 text-muted-foreground" />
                )}
              </span>
            )}
          </button>
        </td>
        <td className="px-4 py-3">
          <StatusBadge status={gen.status} />
        </td>
        <td className="px-4 py-3">
          <span className="text-sm text-white">
            {gen.cost != null ? gen.cost : '--'}
          </span>
        </td>
        <td className="px-4 py-3">
          <span className="text-sm text-muted-foreground">
            {formatDate(gen.created_at)}
          </span>
        </td>
      </tr>
      {expanded && gen.error_message && (
        <tr className="border-b border-surface-lighter/30 bg-destructive-muted/30">
          <td colSpan={6} className="px-4 py-2">
            <p className="text-xs text-destructive font-mono">
              Error: {gen.error_message}
            </p>
          </td>
        </tr>
      )}
    </>
  );
}

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

// --- Table Skeleton ---

function TableSkeleton() {
  return (
    <>
      {Array.from({ length: 8 }).map((_, i) => (
        <tr key={i} className="border-b border-surface-lighter/30">
          {Array.from({ length: 6 }).map((_, j) => (
            <td key={j} className="px-4 py-3">
              <div
                className={cn(
                  'h-4 bg-surface-light rounded animate-pulse-soft',
                  j === 2 ? 'w-40' : 'w-16',
                )}
              />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

// --- Main Page ---

export function GenerationsPage() {
  const [page, setPage] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');

  // Queue status with auto-refresh
  const queueQuery = useQuery({
    queryKey: ['admin', 'generations-queue'],
    queryFn: generationsApi.getQueueStatus,
    refetchInterval: 10_000,
  });

  // Generations list
  const generationsQuery = useQuery({
    queryKey: ['admin', 'generations', page, statusFilter],
    queryFn: () =>
      generationsApi.getGenerations({
        offset: page * PAGE_SIZE,
        limit: PAGE_SIZE,
        status: statusFilter || undefined,
      }),
  });

  const queue = queueQuery.data;
  const generations = generationsQuery.data?.items ?? [];
  const total = generationsQuery.data?.total ?? 0;
  const totalPages = Math.ceil(total / PAGE_SIZE);
  const queueLoading = queueQuery.isLoading;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white">Generations</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Browse and monitor AI image generations across all users.
        </p>
      </div>

      {/* Error banner */}
      {(generationsQuery.isError || queueQuery.isError) && (
        <div className="flex items-center gap-3 bg-destructive-muted border border-destructive/30 text-destructive-foreground rounded-lg px-4 py-3">
          <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0" />
          <p className="text-sm">
            Some data failed to load. Parts of the page may be incomplete.
          </p>
        </div>
      )}

      {/* Queue Status Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <KpiCard
          icon={Activity}
          label="Active"
          value={queue?.active ?? 0}
          loading={queueLoading}
        />
        <KpiCard
          icon={Clock}
          label="Queued"
          value={queue?.queued ?? 0}
          loading={queueLoading}
        />
        <KpiCard
          icon={Play}
          label="Running"
          value={queue?.running ?? 0}
          loading={queueLoading}
        />
      </div>

      {/* Status Filter Tabs */}
      <div className="flex items-center gap-1 p-1 bg-surface rounded-lg w-fit">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => {
              setStatusFilter(tab.value);
              setPage(0);
            }}
            className={cn(
              'px-4 py-1.5 rounded-md text-sm font-medium transition-colors',
              statusFilter === tab.value
                ? 'bg-banana-500 text-dark-500'
                : 'text-muted-foreground hover:text-white hover:bg-surface-light',
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Generations Table */}
      <div className="card-admin overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-surface-lighter/50">
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  User ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Model
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Prompt
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Cost
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Date
                </th>
              </tr>
            </thead>
            <tbody>
              {generationsQuery.isLoading ? (
                <TableSkeleton />
              ) : generations.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center">
                    <div className="flex flex-col items-center">
                      <div className="w-12 h-12 rounded-xl bg-accent-muted flex items-center justify-center mb-3">
                        <Image className="w-6 h-6 text-banana-500" />
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {statusFilter
                          ? `No ${statusFilter} generations found`
                          : 'No generations found'}
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                generations.map((gen) => (
                  <GenerationRow key={gen.id} gen={gen} />
                ))
              )}
            </tbody>
          </table>
        </div>
        <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
      </div>

      {/* Total count footer */}
      {!generationsQuery.isLoading && total > 0 && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Layers className="w-4 h-4" />
          <span>{total.toLocaleString()} total generations{statusFilter ? ` (${statusFilter})` : ''}</span>
        </div>
      )}
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
