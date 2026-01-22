import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../client'
import type {
  StarsPaymentOptionsOut,
  StarsPaymentConfirmIn,
  StarsPaymentConfirmOut,
} from '@/shared/types/api'
import { useUserId } from '@/telegram/hooks'

/**
 * Get Stars payment options
 */
export function usePaymentOptions() {
  return useQuery({
    queryKey: ['payment-options'],
    queryFn: async () => {
      const { data } = await api.get<StarsPaymentOptionsOut>('/payments/stars/options')
      return data
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

/**
 * Confirm Stars payment
 */
export function useConfirmPayment() {
  const queryClient = useQueryClient()
  const telegramId = useUserId()

  return useMutation({
    mutationFn: async (
      params: Omit<StarsPaymentConfirmIn, 'telegram_id'>
    ) => {
      if (!telegramId) throw new Error('No telegram ID')

      const { data } = await api.post<StarsPaymentConfirmOut>(
        '/payments/stars/confirm',
        {
          ...params,
          telegram_id: telegramId,
        }
      )
      return data
    },
    onSuccess: () => {
      // Invalidate balance after payment
      queryClient.invalidateQueries({ queryKey: ['balance'] })
    },
  })
}

/**
 * Calculate credits from stars
 */
export function useCalculateCredits(stars: number) {
  const { data: options } = usePaymentOptions()

  if (!options) return 0

  return Math.floor(
    (stars * options.exchange_numerator) / options.exchange_denominator
  )
}
