import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../client'
import type {
  UserSyncOut,
  BalanceOut,
  TrialStatusOut,
  ReferralInfoOut,
} from '@/shared/types/api'
import { useUserStore } from '@/shared/store/userStore'
import { useUserId } from '@/telegram/hooks'

/**
 * Sync user with backend
 */
export function useSyncUser() {
  const queryClient = useQueryClient()
  const telegramId = useUserId()
  const setTelegramId = useUserStore((s) => s.setTelegramId)

  return useMutation({
    mutationFn: async (referralCode?: string) => {
      if (!telegramId) throw new Error('No telegram ID')

      const { data } = await api.post<UserSyncOut>('/users/sync', {
        telegram_id: telegramId,
        referral_code: referralCode,
      })
      return data
    },
    onSuccess: (data) => {
      setTelegramId(data.telegram_id)
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['balance'] })
      queryClient.invalidateQueries({ queryKey: ['trial'] })
      queryClient.invalidateQueries({ queryKey: ['referral'] })
    },
  })
}

/**
 * Get user balance
 */
export function useBalance() {
  const telegramId = useUserId()
  const setBalance = useUserStore((s) => s.setBalance)

  return useQuery({
    queryKey: ['balance', telegramId],
    queryFn: async () => {
      if (!telegramId) throw new Error('No telegram ID')

      const { data } = await api.get<BalanceOut>(`/users/${telegramId}/balance`)
      setBalance(data.balance)
      return data
    },
    enabled: !!telegramId,
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 60 * 1000, // Refetch every minute
  })
}

/**
 * Get trial status
 */
export function useTrialStatus() {
  const telegramId = useUserId()
  const setTrialAvailable = useUserStore((s) => s.setTrialAvailable)

  return useQuery({
    queryKey: ['trial', telegramId],
    queryFn: async () => {
      if (!telegramId) throw new Error('No telegram ID')

      const { data } = await api.get<TrialStatusOut>(`/users/${telegramId}/trial`)
      setTrialAvailable(data.trial_available)
      return data
    },
    enabled: !!telegramId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

/**
 * Get referral info
 */
export function useReferralInfo() {
  const telegramId = useUserId()
  const setReferralInfo = useUserStore((s) => s.setReferralInfo)

  return useQuery({
    queryKey: ['referral', telegramId],
    queryFn: async () => {
      if (!telegramId) throw new Error('No telegram ID')

      const { data } = await api.get<ReferralInfoOut>(`/referrals/${telegramId}`)
      setReferralInfo({
        referralCode: data.referral_code,
        referralsCount: data.referrals_count,
        referralCreditsTotal: data.referral_credits_total,
        bonusPercent: data.bonus_percent,
      })
      return data
    },
    enabled: !!telegramId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}
