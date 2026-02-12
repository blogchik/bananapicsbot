import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Send,
  Plus,
  Play,
  XCircle,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  MessageSquareText,
} from 'lucide-react';
import { broadcastsApi, type Broadcast } from '@/api/broadcasts';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { cn } from '@/lib/utils';

// --- Helpers ---

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatDateShort(dateStr: string | null): string {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

// --- Sub-components ---

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { bg: string; text: string; dot: string; pulse?: boolean }> = {
    pending: { bg: 'bg-warning-muted', text: 'text-warning', dot: 'bg-warning' },
    running: { bg: 'bg-info-muted', text: 'text-info', dot: 'bg-info', pulse: true },
    completed: { bg: 'bg-success-muted', text: 'text-success', dot: 'bg-success' },
    cancelled: { bg: 'bg-surface-light', text: 'text-muted-foreground', dot: 'bg-muted' },
    failed: { bg: 'bg-destructive-muted', text: 'text-destructive', dot: 'bg-destructive' },
  };

  const c = config[status] ?? config.pending;

  return (
    <span className={cn('inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium', c.bg, c.text)}>
      <span className={cn('w-1.5 h-1.5 rounded-full', c.dot, c.pulse && 'animate-pulse')} />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

function ProgressBar({ sent, total }: { sent: number; total: number }) {
  const percent = total > 0 ? Math.round((sent / total) * 100) : 0;
  return (
    <div className="flex items-center gap-2.5 min-w-[140px]">
      <div className="flex-1 h-1.5 bg-surface-light rounded-full overflow-hidden">
        <div
          className="h-full bg-banana-500 rounded-full transition-all duration-300"
          style={{ width: `${percent}%` }}
        />
      </div>
      <span className="text-xs text-muted-foreground font-mono w-10 text-right">{percent}%</span>
    </div>
  );
}

function FilterBadge({ filterType }: { filterType: string }) {
  const labels: Record<string, string> = {
    all: 'All users',
    active_7d: 'Active 7d',
    active_30d: 'Active 30d',
    with_balance: 'With balance',
    paid_users: 'Paid users',
    new_users: 'New users',
  };
  return (
    <span className="px-2 py-0.5 bg-surface-light rounded text-xs text-muted-foreground">
      {labels[filterType] ?? filterType}
    </span>
  );
}

// --- Skeleton ---

function TableSkeleton() {
  return (
    <div className="card-admin overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-lighter/50">
              {['Type', 'Filter', 'Status', 'Progress', 'Sent / Total', 'Created', 'Actions'].map(
                (h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    {h}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 5 }).map((_, i) => (
              <tr key={i} className="border-b border-surface-lighter/30">
                {Array.from({ length: 7 }).map((_, j) => (
                  <td key={j} className="px-4 py-3.5">
                    <div
                      className="h-4 bg-surface-light rounded animate-pulse-soft"
                      style={{ width: `${50 + Math.random() * 40}%` }}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// --- Main Component ---

export function BroadcastsListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [confirmAction, setConfirmAction] = useState<{
    broadcast: Broadcast;
    action: 'start' | 'cancel';
  } | null>(null);

  // --- Query ---

  const broadcastsQuery = useQuery({
    queryKey: ['admin', 'broadcasts'],
    queryFn: () => broadcastsApi.listBroadcasts(50, 0),
    refetchInterval: 10_000, // Poll frequently for running broadcasts
  });

  // --- Mutations ---

  const startMutation = useMutation({
    mutationFn: (publicId: string) => broadcastsApi.startBroadcast(publicId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'broadcasts'] });
      setConfirmAction(null);
    },
  });

  const cancelMutation = useMutation({
    mutationFn: (publicId: string) => broadcastsApi.cancelBroadcast(publicId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'broadcasts'] });
      setConfirmAction(null);
    },
  });

  const isActionLoading = startMutation.isPending || cancelMutation.isPending;

  // --- Handlers ---

  function handleConfirmAction() {
    if (!confirmAction) return;
    if (confirmAction.action === 'start') {
      startMutation.mutate(confirmAction.broadcast.public_id);
    } else {
      cancelMutation.mutate(confirmAction.broadcast.public_id);
    }
  }

  function toggleExpand(publicId: string) {
    setExpandedId(expandedId === publicId ? null : publicId);
  }

  const broadcasts = broadcastsQuery.data?.broadcasts ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Broadcasts</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Send messages to all or filtered users.
          </p>
        </div>
        <button
          onClick={() => navigate('/broadcasts/new')}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          New Broadcast
        </button>
      </div>

      {/* Error */}
      {broadcastsQuery.isError && (
        <div className="flex items-center gap-3 bg-destructive-muted border border-destructive/30 text-destructive-foreground rounded-lg px-4 py-3">
          <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0" />
          <p className="text-sm">Failed to load broadcasts. Please try again.</p>
        </div>
      )}

      {/* Table */}
      {broadcastsQuery.isLoading ? (
        <TableSkeleton />
      ) : broadcasts.length === 0 ? (
        <div className="card-admin p-12">
          <div className="flex flex-col items-center justify-center text-center">
            <div className="w-14 h-14 rounded-2xl bg-accent-muted flex items-center justify-center mb-4">
              <Send className="w-7 h-7 text-banana-500" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-1">No Broadcasts Yet</h3>
            <p className="text-sm text-muted-foreground max-w-md mb-4">
              Create your first broadcast to send a message to your users.
            </p>
            <button
              onClick={() => navigate('/broadcasts/new')}
              className="btn-primary flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              New Broadcast
            </button>
          </div>
        </div>
      ) : (
        <div className="card-admin overflow-hidden">
          <div className="overflow-x-auto scrollbar-thin">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-lighter/50">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider w-8" />
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Filter</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Progress</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Sent / Total</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Created</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody>
                {broadcasts.map((broadcast) => (
                  <>
                    <tr
                      key={broadcast.public_id}
                      className="border-b border-surface-lighter/30 hover:bg-surface-light/30 transition-colors"
                    >
                      {/* Expand toggle */}
                      <td className="px-4 py-3.5">
                        {broadcast.text && (
                          <button
                            onClick={() => toggleExpand(broadcast.public_id)}
                            className="w-6 h-6 rounded flex items-center justify-center text-muted hover:text-white hover:bg-surface-light transition-colors"
                          >
                            {expandedId === broadcast.public_id ? (
                              <ChevronUp className="w-3.5 h-3.5" />
                            ) : (
                              <ChevronDown className="w-3.5 h-3.5" />
                            )}
                          </button>
                        )}
                      </td>

                      {/* Content type */}
                      <td className="px-4 py-3.5">
                        <span className="inline-flex items-center gap-1.5 text-white text-xs">
                          <MessageSquareText className="w-3.5 h-3.5 text-muted" />
                          {broadcast.content_type}
                        </span>
                      </td>

                      {/* Filter */}
                      <td className="px-4 py-3.5">
                        <FilterBadge filterType={broadcast.filter_type} />
                      </td>

                      {/* Status */}
                      <td className="px-4 py-3.5">
                        <StatusBadge status={broadcast.status} />
                      </td>

                      {/* Progress */}
                      <td className="px-4 py-3.5">
                        <ProgressBar sent={broadcast.sent_count} total={broadcast.total_users} />
                      </td>

                      {/* Sent / Total */}
                      <td className="px-4 py-3.5">
                        <span className="text-white font-mono text-xs">
                          {broadcast.sent_count.toLocaleString()}
                        </span>
                        <span className="text-muted-foreground"> / </span>
                        <span className="text-muted-foreground font-mono text-xs">
                          {broadcast.total_users.toLocaleString()}
                        </span>
                        {broadcast.failed_count > 0 && (
                          <span className="text-destructive text-xs ml-1.5">
                            ({broadcast.failed_count} failed)
                          </span>
                        )}
                      </td>

                      {/* Created */}
                      <td className="px-4 py-3.5 text-muted-foreground text-xs whitespace-nowrap">
                        {formatDateShort(broadcast.created_at)}
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-1">
                          {broadcast.status === 'pending' && (
                            <button
                              onClick={() =>
                                setConfirmAction({ broadcast, action: 'start' })
                              }
                              className="w-8 h-8 rounded-lg flex items-center justify-center text-success hover:bg-success-muted transition-colors"
                              title="Start broadcast"
                            >
                              <Play className="w-4 h-4" />
                            </button>
                          )}
                          {(broadcast.status === 'pending' || broadcast.status === 'running') && (
                            <button
                              onClick={() =>
                                setConfirmAction({ broadcast, action: 'cancel' })
                              }
                              className="w-8 h-8 rounded-lg flex items-center justify-center text-destructive hover:bg-destructive-muted transition-colors"
                              title="Cancel broadcast"
                            >
                              <XCircle className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>

                    {/* Expanded text preview */}
                    {expandedId === broadcast.public_id && broadcast.text && (
                      <tr key={`${broadcast.public_id}-expanded`} className="border-b border-surface-lighter/30">
                        <td colSpan={8} className="px-4 py-4 bg-surface-light/20">
                          <div className="flex gap-3">
                            <div className="w-0.5 bg-banana-500/30 rounded-full flex-shrink-0" />
                            <div className="space-y-2 min-w-0">
                              <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
                                Message Preview
                              </p>
                              <p className="text-sm text-white whitespace-pre-wrap break-words leading-relaxed">
                                {broadcast.text}
                              </p>
                              {broadcast.inline_button_text && (
                                <div className="pt-1">
                                  <span className="inline-flex items-center gap-1 px-3 py-1.5 bg-info-muted text-info text-xs font-medium rounded-lg">
                                    {broadcast.inline_button_text}
                                    {broadcast.inline_button_url && (
                                      <span className="text-info/50 ml-1">
                                        ({broadcast.inline_button_url})
                                      </span>
                                    )}
                                  </span>
                                </div>
                              )}
                              {/* Stats for completed */}
                              {broadcast.completed_at && (
                                <p className="text-xs text-muted-foreground">
                                  Completed: {formatDate(broadcast.completed_at)}
                                  {broadcast.blocked_count > 0 && (
                                    <span className="ml-2">
                                      Blocked: <span className="text-warning">{broadcast.blocked_count}</span>
                                    </span>
                                  )}
                                </p>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Confirm Dialog */}
      <ConfirmDialog
        open={confirmAction !== null}
        title={
          confirmAction?.action === 'start'
            ? 'Start this broadcast?'
            : 'Cancel this broadcast?'
        }
        description={
          confirmAction?.action === 'start'
            ? `This will start sending the broadcast to ${confirmAction.broadcast.total_users.toLocaleString()} users. This action cannot be undone.`
            : 'This will stop the broadcast. Users who have already received the message will keep it.'
        }
        confirmLabel={confirmAction?.action === 'start' ? 'Start Broadcast' : 'Cancel Broadcast'}
        variant={confirmAction?.action === 'cancel' ? 'destructive' : 'default'}
        loading={isActionLoading}
        onConfirm={handleConfirmAction}
        onCancel={() => setConfirmAction(null)}
      />
    </div>
  );
}
