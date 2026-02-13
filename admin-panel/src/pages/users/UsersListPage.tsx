import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Users, ShieldBan, ShieldCheck, AlertCircle } from 'lucide-react';
import { usersApi, type AdminUser } from '@/api/users';
import { DataTable, type Column, type PaginationState } from '@/components/DataTable';
import { SearchInput } from '@/components/SearchInput';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { cn } from '@/lib/utils';

const PAGE_SIZE = 50;

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function StatusBadge({ banned }: { banned: boolean }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium',
        banned
          ? 'bg-destructive-muted text-destructive'
          : 'bg-success-muted text-success',
      )}
    >
      <span
        className={cn(
          'w-1.5 h-1.5 rounded-full',
          banned ? 'bg-destructive' : 'bg-success',
        )}
      />
      {banned ? 'Banned' : 'Active'}
    </span>
  );
}

export function UsersListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [searchQuery, setSearchQuery] = useState('');
  const [offset, setOffset] = useState(0);
  const [confirmAction, setConfirmAction] = useState<{
    user: AdminUser;
    action: 'ban' | 'unban';
  } | null>(null);

  // --- Queries ---

  const usersQuery = useQuery({
    queryKey: ['admin', 'users', searchQuery, offset],
    queryFn: () => usersApi.searchUsers(searchQuery || undefined, offset, PAGE_SIZE),
    placeholderData: (previousData) => previousData,
  });

  // --- Mutations ---

  const banMutation = useMutation({
    mutationFn: (telegramId: number) => usersApi.banUser(telegramId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      setConfirmAction(null);
    },
  });

  const unbanMutation = useMutation({
    mutationFn: (telegramId: number) => usersApi.unbanUser(telegramId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      setConfirmAction(null);
    },
  });

  const isActionLoading = banMutation.isPending || unbanMutation.isPending;

  // --- Handlers ---

  const handleSearch = useCallback((value: string) => {
    setSearchQuery(value);
    setOffset(0);
  }, []);

  function handleRowClick(user: AdminUser) {
    navigate(`/users/${user.telegram_id}`);
  }

  function handleConfirmAction() {
    if (!confirmAction) return;
    if (confirmAction.action === 'ban') {
      banMutation.mutate(confirmAction.user.telegram_id);
    } else {
      unbanMutation.mutate(confirmAction.user.telegram_id);
    }
  }

  // --- Columns ---

  const columns: Column<AdminUser>[] = [
    {
      key: 'user',
      header: 'User',
      render: (user) => (
        <div className="flex items-center gap-3">
          {/* Avatar */}
          {user.photo_url ? (
            <img
              src={user.photo_url}
              alt=""
              className="w-8 h-8 rounded-full object-cover flex-shrink-0"
            />
          ) : (
            <div className="w-8 h-8 rounded-full bg-surface-light flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-medium text-muted-foreground">
                {(user.first_name?.[0] || user.username?.[0] || '?').toUpperCase()}
              </span>
            </div>
          )}
          <div className="min-w-0">
            <p className="text-sm font-medium text-white truncate">
              {user.first_name || user.last_name
                ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
                : user.username
                  ? `@${user.username}`
                  : `User ${user.telegram_id}`}
            </p>
            {user.username && (user.first_name || user.last_name) && (
              <p className="text-xs text-muted-foreground">@{user.username}</p>
            )}
          </div>
        </div>
      ),
    },
    {
      key: 'telegram_id',
      header: 'Telegram ID',
      render: (user) => (
        <span className="font-mono text-sm text-banana-500">{user.telegram_id}</span>
      ),
    },
    {
      key: 'balance',
      header: 'Balance',
      render: (user) => (
        <span className="font-medium text-white">{user.balance.toLocaleString()}</span>
      ),
    },
    {
      key: 'generation_count',
      header: 'Generations',
      render: (user) => (
        <span className="text-muted-foreground">{user.generation_count.toLocaleString()}</span>
      ),
    },
    {
      key: 'referral_count',
      header: 'Referrals',
      render: (user) => (
        <span className="text-muted-foreground">{user.referral_count}</span>
      ),
    },
    {
      key: 'created_at',
      header: 'Created',
      render: (user) => (
        <span className="text-muted-foreground text-xs">{formatDate(user.created_at)}</span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (user) => <StatusBadge banned={user.is_banned} />,
    },
    {
      key: 'actions',
      header: '',
      width: '60px',
      render: (user) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            setConfirmAction({
              user,
              action: user.is_banned ? 'unban' : 'ban',
            });
          }}
          className={cn(
            'w-8 h-8 rounded-lg flex items-center justify-center transition-colors',
            user.is_banned
              ? 'text-success hover:bg-success-muted'
              : 'text-destructive hover:bg-destructive-muted',
          )}
          title={user.is_banned ? 'Unban user' : 'Ban user'}
        >
          {user.is_banned ? (
            <ShieldCheck className="w-4 h-4" />
          ) : (
            <ShieldBan className="w-4 h-4" />
          )}
        </button>
      ),
    },
  ];

  // --- Pagination ---

  const pagination: PaginationState | undefined = usersQuery.data
    ? {
        offset: usersQuery.data.offset,
        limit: usersQuery.data.limit,
        total: usersQuery.data.total,
      }
    : undefined;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Users</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Manage and view all registered users.
          </p>
        </div>
        {usersQuery.data && (
          <div className="text-sm text-muted-foreground">
            <span className="text-white font-medium">{usersQuery.data.total.toLocaleString()}</span> total users
          </div>
        )}
      </div>

      {/* Search */}
      <SearchInput
        placeholder="Search by Telegram ID, username, or referral code..."
        onChange={handleSearch}
      />

      {/* Error */}
      {usersQuery.isError && (
        <div className="flex items-center gap-3 bg-destructive-muted border border-destructive/30 text-destructive-foreground rounded-lg px-4 py-3">
          <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0" />
          <p className="text-sm">Failed to load users. Please try again.</p>
        </div>
      )}

      {/* Table */}
      <DataTable
        columns={columns}
        data={usersQuery.data?.users ?? []}
        loading={usersQuery.isLoading}
        pagination={pagination}
        onPageChange={setOffset}
        onRowClick={handleRowClick}
        emptyMessage="No users found matching your search."
        emptyIcon={
          <div className="w-12 h-12 rounded-xl bg-accent-muted flex items-center justify-center mb-3">
            <Users className="w-6 h-6 text-banana-500" />
          </div>
        }
        rowKey={(user) => user.telegram_id}
      />

      {/* Confirm Dialog */}
      <ConfirmDialog
        open={confirmAction !== null}
        title={
          confirmAction?.action === 'ban'
            ? `Ban user ${confirmAction.user.telegram_id}?`
            : `Unban user ${confirmAction?.user.telegram_id}?`
        }
        description={
          confirmAction?.action === 'ban'
            ? 'This user will be banned from using the bot. They will not be able to generate images or make purchases.'
            : 'This user will be unbanned and can resume using the bot normally.'
        }
        confirmLabel={confirmAction?.action === 'ban' ? 'Ban User' : 'Unban User'}
        variant={confirmAction?.action === 'ban' ? 'destructive' : 'default'}
        loading={isActionLoading}
        onConfirm={handleConfirmAction}
        onCancel={() => setConfirmAction(null)}
      />
    </div>
  );
}
