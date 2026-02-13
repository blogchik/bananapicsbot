import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Clock,
  Play,
  Layers,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Image,
  X,
  CheckCircle2,
  XCircle,
  User,
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { cn } from '@/lib/utils';
import { generationsApi, type AdminGeneration } from '@/api/generations';

const PAGE_SIZE = 50;


// --- Helpers ---

function formatDate(dateStr: string): string {
  try {
    return format(parseISO(dateStr), 'MMM d, yyyy HH:mm');
  } catch {
    return dateStr;
  }
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

// --- User Profile Cache ---
const userProfileCache: Record<number, { first_name?: string; username?: string; photo_url?: string }> = {};

async function fetchUserProfile(telegramId: number): Promise<{ first_name?: string; username?: string; photo_url?: string }> {
  if (userProfileCache[telegramId]) {
    return userProfileCache[telegramId];
  }
  try {
    const response = await fetch(`/api/v1/admin/users/${telegramId}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
      },
    });
    if (response.ok) {
      const data = await response.json();
      const profile = {
        first_name: data.first_name || data.username || `User`,
        username: data.username,
        photo_url: data.photo_url,
      };
      userProfileCache[telegramId] = profile;
      return profile;
    }
  } catch (e) {
    console.error('Failed to fetch user profile', e);
  }
  return { first_name: 'User' };
}

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

// --- Image Preview Modal ---

function ImagePreviewModal({
  images,
  onClose,
}: {
  images: string[];
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <button
        onClick={onClose}
        className="absolute top-4 right-4 w-10 h-10 rounded-lg bg-surface-light/80 flex items-center justify-center hover:bg-surface-lighter transition-colors z-10"
      >
        <X className="w-5 h-5 text-white" />
      </button>
      <div
        className="relative flex flex-wrap gap-4 justify-center items-center max-h-[90vh] overflow-auto p-4"
        onClick={(e) => e.stopPropagation()}
      >
        {images.map((url, i) => (
          <img
            key={i}
            src={url}
            alt={`Result ${i + 1}`}
            className="rounded-lg max-h-[80vh] object-contain shadow-xl"
            style={{ maxWidth: 'min(100%, 800px)' }}
          />
        ))}
      </div>
    </div>
  );
}

// --- User Cell Component ---

function UserCell({ telegramId }: { telegramId: number }) {
  const [profile, setProfile] = useState<{ first_name?: string; username?: string; photo_url?: string } | null>(
    userProfileCache[telegramId] || null
  );

  useEffect(() => {
    if (!profile) {
      fetchUserProfile(telegramId).then(setProfile);
    }
  }, [telegramId, profile]);

  const name = profile?.first_name || 'Loading...';
  const initials = getInitials(name);

  return (
    <Link
      to={`/users/${telegramId}`}
      className="flex items-center gap-3 group"
    >
      {profile?.photo_url ? (
        <img
          src={profile.photo_url}
          alt={name}
          className="w-8 h-8 rounded-full object-cover ring-2 ring-surface-lighter group-hover:ring-banana-500 transition-all"
        />
      ) : (
        <div className="w-8 h-8 rounded-full bg-surface-light flex items-center justify-center text-xs font-medium text-muted-foreground group-hover:bg-banana-500/20 group-hover:text-banana-500 transition-all">
          {profile ? initials : <User className="w-4 h-4" />}
        </div>
      )}
      <div className="min-w-0">
        <p className="text-sm font-medium text-white truncate group-hover:text-banana-400 transition-colors">
          {name}
        </p>
        {profile?.username && (
          <p className="text-xs text-muted-foreground truncate">@{profile.username}</p>
        )}
      </div>
    </Link>
  );
}

// --- Generation Row ---

function GenerationRow({ gen }: { gen: AdminGeneration }) {
  const [expanded, setExpanded] = useState(false);
  const [showImages, setShowImages] = useState(false);
  const maxLength = 60;
  const isLongPrompt = gen.prompt.length > maxLength;
  const displayPrompt = expanded || !isLongPrompt
    ? gen.prompt
    : gen.prompt.slice(0, maxLength) + '...';
  const hasImages = gen.result_urls && gen.result_urls.length > 0;

  return (
    <>
      <tr className="border-b border-surface-lighter/30 hover:bg-surface-light/30 transition-colors">
        <td className="px-4 py-3">
          <UserCell telegramId={gen.telegram_id} />
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
          {hasImages ? (
            <div className="flex items-center gap-1">
              {gen.result_urls.slice(0, 3).map((url, idx) => (
                <button
                  key={idx}
                  onClick={() => setShowImages(true)}
                  className="w-8 h-8 rounded overflow-hidden border border-surface-lighter hover:border-banana-500 transition-colors"
                >
                  <img src={url} alt="" className="w-full h-full object-cover" />
                </button>
              ))}
              {gen.result_urls.length > 3 && (
                <button
                  onClick={() => setShowImages(true)}
                  className="w-8 h-8 rounded bg-surface-light flex items-center justify-center text-xs text-muted-foreground hover:text-white transition-colors"
                >
                  +{gen.result_urls.length - 3}
                </button>
              )}
            </div>
          ) : (
            <span className="text-sm text-muted">--</span>
          )}
        </td>
        <td className="px-4 py-3">
          <span className="text-sm text-muted-foreground">
            {formatDate(gen.created_at)}
          </span>
        </td>
      </tr>
      {expanded && gen.full_prompt && (
        <tr className="border-b border-surface-lighter/30 bg-surface-light/20">
          <td colSpan={7} className="px-4 py-3">
            <p className="text-sm text-white whitespace-pre-wrap">
              {gen.full_prompt}
            </p>
          </td>
        </tr>
      )}
      {showImages && hasImages && (
        <ImagePreviewModal
          images={gen.result_urls}
          onClose={() => setShowImages(false)}
        />
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
          {Array.from({ length: 7 }).map((_, j) => (
            <td key={j} className="px-4 py-3">
              <div
                className={cn(
                  'h-4 bg-surface-light rounded animate-pulse-soft',
                  j === 0 ? 'w-32' : j === 2 ? 'w-40' : 'w-16',
                )}
              />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

// --- Status Count Card ---

function StatusCountCard({
  label,
  count,
  icon: Icon,
  color,
  active,
  onClick,
}: {
  label: string;
  count: number;
  icon: typeof Clock;
  color: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'p-4 rounded-xl border transition-all text-left',
        active
          ? 'bg-banana-500/10 border-banana-500/50'
          : 'bg-surface border-surface-lighter/30 hover:border-surface-lighter',
      )}
    >
      <div className="flex items-center gap-3">
        <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center',
          active ? 'bg-banana-500/20' : 'bg-surface-light')}>
          <Icon className={cn('w-5 h-5', active ? 'text-banana-500' : color)} />
        </div>
        <div>
          <p className="text-2xl font-bold text-white">{count.toLocaleString()}</p>
          <p className="text-xs text-muted-foreground">{label}</p>
        </div>
      </div>
    </button>
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

  const handleStatusFilter = (status: string) => {
    setStatusFilter(status);
    setPage(0);
  };

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

      {/* Status Count Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <StatusCountCard
          label="All"
          count={(queue?.completed ?? 0) + (queue?.failed ?? 0) + (queue?.running ?? 0) + (queue?.queued ?? 0)}
          icon={Layers}
          color="text-muted-foreground"
          active={statusFilter === ''}
          onClick={() => handleStatusFilter('')}
        />
        <StatusCountCard
          label="Completed"
          count={queue?.completed ?? 0}
          icon={CheckCircle2}
          color="text-success"
          active={statusFilter === 'completed'}
          onClick={() => handleStatusFilter('completed')}
        />
        <StatusCountCard
          label="Failed"
          count={queue?.failed ?? 0}
          icon={XCircle}
          color="text-destructive"
          active={statusFilter === 'failed'}
          onClick={() => handleStatusFilter('failed')}
        />
        <StatusCountCard
          label="Running"
          count={queue?.running ?? 0}
          icon={Play}
          color="text-info"
          active={statusFilter === 'running'}
          onClick={() => handleStatusFilter('running')}
        />
        <StatusCountCard
          label="Queued"
          count={queue?.queued ?? 0}
          icon={Clock}
          color="text-warning"
          active={statusFilter === 'queued'}
          onClick={() => handleStatusFilter('queued')}
        />
      </div>

      {/* Generations Table */}
      <div className="card-admin overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-surface-lighter/50">
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  User
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
                  Images
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
                  <td colSpan={7} className="px-4 py-12 text-center">
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
