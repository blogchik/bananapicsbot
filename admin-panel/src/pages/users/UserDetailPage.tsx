import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  User,
  Wallet,
  Image,
  Users,
  Calendar,
  ShieldBan,
  ShieldCheck,
  AlertCircle,
  Coins,
  CreditCard,
  Hash,
  Clock,
  Sparkles,
  Globe,
  Link2,
  TrendingDown,
  ExternalLink,
  Star,
} from 'lucide-react';
import { usersApi, type UserGeneration, type UserPayment } from '@/api/users';
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

// --- Skeleton ---

function ProfileSkeleton() {
  return (
    <div className="card-admin p-6">
      <div className="flex items-center gap-4 mb-6">
        <div className="w-14 h-14 rounded-2xl bg-surface-light animate-pulse-soft" />
        <div className="space-y-2">
          <div className="h-5 w-40 bg-surface-light rounded animate-pulse-soft" />
          <div className="h-4 w-24 bg-surface-light rounded animate-pulse-soft" />
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="space-y-1.5">
            <div className="h-3 w-16 bg-surface-light rounded animate-pulse-soft" />
            <div className="h-5 w-20 bg-surface-light rounded animate-pulse-soft" />
          </div>
        ))}
      </div>
    </div>
  );
}

// --- Sub-components ---

function StatItem({
  icon: Icon,
  label,
  value,
  className,
}: {
  icon: typeof User;
  label: string;
  value: string | number;
  className?: string;
}) {
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-1.5">
        <Icon className="w-3.5 h-3.5 text-muted" />
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
      <p className={cn('text-sm font-medium text-white', className)}>
        {typeof value === 'number' ? value.toLocaleString() : value}
      </p>
    </div>
  );
}

function GenerationStatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: 'bg-success-muted text-success',
    failed: 'bg-destructive-muted text-destructive',
    pending: 'bg-warning-muted text-warning',
    processing: 'bg-info-muted text-info',
  };
  return (
    <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', styles[status] ?? 'bg-surface-light text-muted-foreground')}>
      {status}
    </span>
  );
}

function PaymentStatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: 'bg-success-muted text-success',
    failed: 'bg-destructive-muted text-destructive',
    pending: 'bg-warning-muted text-warning',
    refunded: 'bg-info-muted text-info',
  };
  return (
    <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', styles[status] ?? 'bg-surface-light text-muted-foreground')}>
      {status}
    </span>
  );
}

// --- Main Component ---

export function UserDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const telegramId = Number(id);

  const [activeTab, setActiveTab] = useState<'generations' | 'payments'>('generations');
  const [showBanConfirm, setShowBanConfirm] = useState(false);

  // Credit adjustment form
  const [creditAmount, setCreditAmount] = useState('');
  const [creditReason, setCreditReason] = useState('');

  // --- Queries ---

  const userQuery = useQuery({
    queryKey: ['admin', 'user', telegramId],
    queryFn: () => usersApi.getUser(telegramId),
    enabled: !isNaN(telegramId),
  });

  const generationsQuery = useQuery({
    queryKey: ['admin', 'user', telegramId, 'generations'],
    queryFn: () => usersApi.getUserGenerations(telegramId, 20),
    enabled: !isNaN(telegramId) && activeTab === 'generations',
  });

  const paymentsQuery = useQuery({
    queryKey: ['admin', 'user', telegramId, 'payments'],
    queryFn: () => usersApi.getUserPayments(telegramId, 20),
    enabled: !isNaN(telegramId) && activeTab === 'payments',
  });

  // --- Mutations ---

  const banMutation = useMutation({
    mutationFn: () =>
      userQuery.data?.is_banned
        ? usersApi.unbanUser(telegramId)
        : usersApi.banUser(telegramId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'user', telegramId] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      setShowBanConfirm(false);
    },
  });

  const creditMutation = useMutation({
    mutationFn: () =>
      usersApi.adjustCredits(telegramId, Number(creditAmount), creditReason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'user', telegramId] });
      setCreditAmount('');
      setCreditReason('');
    },
  });

  const user = userQuery.data;
  const isCreditFormValid =
    creditAmount !== '' &&
    !isNaN(Number(creditAmount)) &&
    Number(creditAmount) !== 0 &&
    creditReason.trim().length > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/users')}
          className="w-9 h-9 rounded-lg bg-surface-light flex items-center justify-center hover:bg-surface-lighter transition-colors"
        >
          <ArrowLeft className="w-4 h-4 text-muted-foreground" />
        </button>
        <div>
          <h2 className="text-2xl font-bold text-white">User Detail</h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            Telegram ID: <span className="font-mono text-banana-500">{id}</span>
          </p>
        </div>
      </div>

      {/* Error */}
      {userQuery.isError && (
        <div className="flex items-center gap-3 bg-destructive-muted border border-destructive/30 text-destructive-foreground rounded-lg px-4 py-3">
          <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0" />
          <p className="text-sm">Failed to load user details. The user may not exist.</p>
        </div>
      )}

      {/* Profile Card */}
      {userQuery.isLoading ? (
        <ProfileSkeleton />
      ) : user ? (
        <div className="card-admin p-6">
          {/* User header */}
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center gap-4">
              {/* Avatar */}
              {user.photo_url ? (
                <img
                  src={user.photo_url}
                  alt=""
                  className="w-16 h-16 rounded-2xl object-cover flex-shrink-0"
                />
              ) : (
                <div className="w-16 h-16 rounded-2xl bg-accent-muted flex items-center justify-center flex-shrink-0">
                  <span className="text-2xl font-bold text-banana-500">
                    {(user.first_name?.[0] || user.username?.[0] || '?').toUpperCase()}
                  </span>
                </div>
              )}
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-semibold text-white">
                    {user.first_name || user.last_name
                      ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
                      : user.username
                        ? `@${user.username}`
                        : `User ${user.telegram_id}`}
                  </h3>
                  <span
                    className={cn(
                      'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium',
                      user.is_banned
                        ? 'bg-destructive-muted text-destructive'
                        : 'bg-success-muted text-success',
                    )}
                  >
                    <span
                      className={cn(
                        'w-1.5 h-1.5 rounded-full',
                        user.is_banned ? 'bg-destructive' : 'bg-success',
                      )}
                    />
                    {user.is_banned ? 'Banned' : 'Active'}
                  </span>
                </div>
                {user.username && (
                  <p className="text-sm text-muted-foreground mt-0.5">@{user.username}</p>
                )}
                {user.language_code && (
                  <div className="flex items-center gap-1 mt-1">
                    <Globe className="w-3 h-3 text-muted" />
                    <span className="text-xs text-muted-foreground uppercase">{user.language_code}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Ban/Unban button */}
            <button
              onClick={() => setShowBanConfirm(true)}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                user.is_banned
                  ? 'bg-success-muted text-success hover:bg-success/20'
                  : 'bg-destructive-muted text-destructive hover:bg-destructive/20',
              )}
            >
              {user.is_banned ? (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  Unban
                </>
              ) : (
                <>
                  <ShieldBan className="w-4 h-4" />
                  Ban
                </>
              )}
            </button>
          </div>

          {/* Stats grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
            <StatItem icon={Hash} label="Telegram ID" value={user.telegram_id} className="font-mono text-banana-500" />
            <StatItem icon={Wallet} label="Balance" value={`${user.balance} credits`} />
            <StatItem icon={Sparkles} label="Trial Remaining" value={user.trial_remaining} />
            <StatItem icon={Image} label="Generations" value={user.generation_count} />
            <StatItem icon={Users} label="Referrals" value={user.referral_count} />
            <StatItem icon={Star} label="Total Deposits" value={`${user.total_deposits || 0} stars`} />
            <StatItem icon={TrendingDown} label="Total Spent" value={`${user.total_spent || 0} credits`} />
            <StatItem icon={Calendar} label="Joined" value={formatDateShort(user.created_at)} />
            <StatItem icon={Clock} label="Last Active" value={formatDateShort(user.last_active_at)} />
            {user.referral_code && (
              <StatItem icon={Link2} label="Referral Code" value={user.referral_code} className="font-mono" />
            )}
          </div>

          {/* Referrer info */}
          {user.referrer_id && (
            <div className="mt-4 bg-surface-light/50 rounded-lg px-4 py-3">
              <p className="text-xs text-muted-foreground mb-1">Referred By</p>
              <a
                href={`/users/${user.referrer_id}`}
                className="text-sm text-banana-500 hover:text-banana-400 font-mono flex items-center gap-1"
              >
                {user.referrer_id}
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          )}

          {/* Ban reason */}
          {user.is_banned && user.ban_reason && (
            <div className="mt-4 bg-destructive-muted border border-destructive/20 rounded-lg px-4 py-3">
              <p className="text-xs text-muted-foreground mb-1">Ban Reason</p>
              <p className="text-sm text-destructive">{user.ban_reason}</p>
            </div>
          )}
        </div>
      ) : null}

      {/* Credit Adjustment */}
      {user && (
        <div className="card-admin p-6">
          <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
            <Coins className="w-4 h-4 text-banana-500" />
            Credit Adjustment
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-muted-foreground mb-1.5">Amount</label>
              <input
                type="number"
                value={creditAmount}
                onChange={(e) => setCreditAmount(e.target.value)}
                placeholder="e.g. 100 or -50"
                className="w-full bg-surface border border-surface-lighter/50 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-muted focus-ring hover:border-banana-500/30 transition-colors"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Use positive to add, negative to deduct.
              </p>
            </div>
            <div className="md:col-span-2">
              <label className="block text-xs text-muted-foreground mb-1.5">Reason</label>
              <div className="flex gap-3">
                <textarea
                  value={creditReason}
                  onChange={(e) => setCreditReason(e.target.value)}
                  placeholder="Reason for the adjustment..."
                  rows={1}
                  className="flex-1 bg-surface border border-surface-lighter/50 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-muted focus-ring hover:border-banana-500/30 transition-colors resize-none"
                />
                <button
                  onClick={() => creditMutation.mutate()}
                  disabled={!isCreditFormValid || creditMutation.isPending}
                  className="btn-primary whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {creditMutation.isPending ? 'Adjusting...' : 'Adjust Credits'}
                </button>
              </div>
            </div>
          </div>

          {/* Success feedback */}
          {creditMutation.isSuccess && (
            <div className="mt-3 flex items-center gap-2 text-sm text-success">
              <ShieldCheck className="w-4 h-4" />
              Credits adjusted successfully.
            </div>
          )}

          {/* Error feedback */}
          {creditMutation.isError && (
            <div className="mt-3 flex items-center gap-2 text-sm text-destructive">
              <AlertCircle className="w-4 h-4" />
              Failed to adjust credits. Please try again.
            </div>
          )}
        </div>
      )}

      {/* Tabs: Generations / Payments */}
      {user && (
        <div className="space-y-4">
          {/* Tab header */}
          <div className="flex items-center gap-1 border-b border-surface-lighter/50">
            <button
              onClick={() => setActiveTab('generations')}
              className={cn(
                'px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px',
                activeTab === 'generations'
                  ? 'text-banana-500 border-banana-500'
                  : 'text-muted-foreground border-transparent hover:text-white',
              )}
            >
              <span className="inline-flex items-center gap-2">
                <Image className="w-4 h-4" />
                Generations
              </span>
            </button>
            <button
              onClick={() => setActiveTab('payments')}
              className={cn(
                'px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px',
                activeTab === 'payments'
                  ? 'text-banana-500 border-banana-500'
                  : 'text-muted-foreground border-transparent hover:text-white',
              )}
            >
              <span className="inline-flex items-center gap-2">
                <CreditCard className="w-4 h-4" />
                Payments
              </span>
            </button>
          </div>

          {/* Generations Tab */}
          {activeTab === 'generations' && (
            <div className="card-admin overflow-hidden">
              {generationsQuery.isLoading ? (
                <div className="p-6 space-y-3">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="flex gap-4">
                      <div className="h-4 w-24 bg-surface-light rounded animate-pulse-soft" />
                      <div className="h-4 flex-1 bg-surface-light rounded animate-pulse-soft" />
                      <div className="h-4 w-20 bg-surface-light rounded animate-pulse-soft" />
                      <div className="h-4 w-16 bg-surface-light rounded animate-pulse-soft" />
                    </div>
                  ))}
                </div>
              ) : (generationsQuery.data ?? []).length === 0 ? (
                <div className="p-12 text-center">
                  <Image className="w-8 h-8 text-muted mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">No generations found for this user.</p>
                </div>
              ) : (
                <div className="space-y-4 p-4">
                  {(generationsQuery.data ?? []).map((gen: UserGeneration) => (
                    <div key={gen.id} className="bg-surface-light/30 rounded-lg p-4 space-y-3">
                      {/* Header row */}
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="flex items-center gap-3">
                          <div className="flex flex-col">
                            <span className="text-sm font-medium text-white">{gen.model_name}</span>
                            <span className="text-xs text-muted-foreground font-mono">{gen.model_key}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          {gen.cost != null && (
                            <span className="text-sm font-mono text-banana-400">{gen.cost} credits</span>
                          )}
                          <GenerationStatusBadge status={gen.status} />
                          <span className="text-xs text-muted-foreground">{formatDateShort(gen.created_at)}</span>
                        </div>
                      </div>

                      {/* Prompt */}
                      {gen.prompt && (
                        <p className="text-sm text-muted-foreground line-clamp-2" title={gen.full_prompt || gen.prompt}>
                          {gen.prompt}
                        </p>
                      )}

                      {/* Images */}
                      {gen.result_urls && gen.result_urls.length > 0 && (
                        <div className="flex gap-2 flex-wrap">
                          {gen.result_urls.map((url, idx) => (
                            <a
                              key={idx}
                              href={url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="block w-20 h-20 rounded-lg overflow-hidden border border-surface-lighter hover:border-banana-500 transition-colors"
                            >
                              <img
                                src={url}
                                alt={`Result ${idx + 1}`}
                                className="w-full h-full object-cover"
                              />
                            </a>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Payments Tab */}
          {activeTab === 'payments' && (
            <div className="card-admin overflow-hidden">
              {paymentsQuery.isLoading ? (
                <div className="p-6 space-y-3">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="flex gap-4">
                      <div className="h-4 w-20 bg-surface-light rounded animate-pulse-soft" />
                      <div className="h-4 w-24 bg-surface-light rounded animate-pulse-soft" />
                      <div className="h-4 w-16 bg-surface-light rounded animate-pulse-soft" />
                      <div className="h-4 w-20 bg-surface-light rounded animate-pulse-soft" />
                    </div>
                  ))}
                </div>
              ) : (paymentsQuery.data ?? []).length === 0 ? (
                <div className="p-12 text-center">
                  <CreditCard className="w-8 h-8 text-muted mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">No payments found for this user.</p>
                </div>
              ) : (
                <div className="overflow-x-auto scrollbar-thin">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-surface-lighter/50">
                        <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Stars</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Credits</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(paymentsQuery.data ?? []).map((payment: UserPayment) => (
                        <tr key={payment.id} className="border-b border-surface-lighter/30">
                          <td className="px-4 py-3 text-banana-500 font-medium">
                            {payment.stars_amount.toLocaleString()} stars
                          </td>
                          <td className="px-4 py-3 text-white font-mono text-xs">
                            {payment.credits_amount.toLocaleString()}
                          </td>
                          <td className="px-4 py-3">
                            <PaymentStatusBadge status={payment.status} />
                          </td>
                          <td className="px-4 py-3 text-muted-foreground text-xs whitespace-nowrap">
                            {formatDate(payment.created_at)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Ban/Unban Confirm Dialog */}
      <ConfirmDialog
        open={showBanConfirm}
        title={
          user?.is_banned
            ? `Unban user ${user.telegram_id}?`
            : `Ban user ${user?.telegram_id}?`
        }
        description={
          user?.is_banned
            ? 'This user will be unbanned and can resume using the bot normally.'
            : 'This user will be banned from using the bot. They will not be able to generate images or make purchases.'
        }
        confirmLabel={user?.is_banned ? 'Unban User' : 'Ban User'}
        variant={user?.is_banned ? 'default' : 'destructive'}
        loading={banMutation.isPending}
        onConfirm={() => banMutation.mutate()}
        onCancel={() => setShowBanConfirm(false)}
      />
    </div>
  );
}
