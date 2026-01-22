import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../client'
import type {
  GenerationSubmitIn,
  GenerationSubmitOut,
  GenerationActiveOut,
  GenerationResultsOut,
  GenerationRequestOut,
  PriceCalculateIn,
  PriceCalculateOut,
} from '@/shared/types/api'
import { useUserId } from '@/telegram/hooks'
import { useGenerationStore } from '@/shared/store/generationStore'

/**
 * Calculate generation price
 */
export function useCalculatePrice() {
  const telegramId = useUserId()
  const setCalculatedPrice = useGenerationStore((s) => s.setCalculatedPrice)

  return useMutation({
    mutationFn: async (params: Omit<PriceCalculateIn, 'telegram_id'>) => {
      if (!telegramId) throw new Error('No telegram ID')

      const { data } = await api.post<PriceCalculateOut>('/generations/price', {
        ...params,
        telegram_id: telegramId,
      })
      return data
    },
    onSuccess: (data) => {
      setCalculatedPrice(data.price_credits, data.has_balance || data.trial_available)
    },
  })
}

/**
 * Submit generation request
 */
export function useSubmitGeneration() {
  const queryClient = useQueryClient()
  const telegramId = useUserId()
  const setActiveGeneration = useGenerationStore((s) => s.setActiveGeneration)

  return useMutation({
    mutationFn: async (params: Omit<GenerationSubmitIn, 'telegram_id'>) => {
      if (!telegramId) throw new Error('No telegram ID')

      const { data } = await api.post<GenerationSubmitOut>('/generations/submit', {
        ...params,
        telegram_id: telegramId,
      })
      return data
    },
    onSuccess: (data) => {
      setActiveGeneration({
        requestId: data.request.id,
        publicId: data.request.public_id,
        status: data.request.status,
      })

      // Invalidate balance and trial
      queryClient.invalidateQueries({ queryKey: ['balance'] })
      queryClient.invalidateQueries({ queryKey: ['trial'] })
      queryClient.invalidateQueries({ queryKey: ['active-generation'] })
    },
  })
}

/**
 * Get active generation status
 */
export function useActiveGeneration() {
  const telegramId = useUserId()
  const setActiveGeneration = useGenerationStore((s) => s.setActiveGeneration)

  return useQuery({
    queryKey: ['active-generation', telegramId],
    queryFn: async () => {
      if (!telegramId) throw new Error('No telegram ID')

      const { data } = await api.get<GenerationActiveOut>(`/generations/active`, {
        params: { telegram_id: telegramId },
      })

      if (data.has_active && data.request_id && data.public_id && data.status) {
        setActiveGeneration({
          requestId: data.request_id,
          publicId: data.public_id,
          status: data.status,
        })
      } else {
        setActiveGeneration(null)
      }

      return data
    },
    enabled: !!telegramId,
    refetchInterval: (query) => {
      // Poll more frequently if there's an active generation
      const data = query.state.data
      if (data?.has_active && data.status !== 'completed' && data.status !== 'failed') {
        return 2000 // 2 seconds
      }
      return false
    },
  })
}

/**
 * Get generation by public ID
 */
export function useGeneration(publicId: string | null) {
  return useQuery({
    queryKey: ['generation', publicId],
    queryFn: async () => {
      if (!publicId) throw new Error('No public ID')

      const { data } = await api.get<GenerationRequestOut>(`/generations/${publicId}`)
      return data
    },
    enabled: !!publicId,
    refetchInterval: (query) => {
      const data = query.state.data
      if (data && data.status !== 'completed' && data.status !== 'failed') {
        return 2000 // Poll while in progress
      }
      return false
    },
  })
}

/**
 * Get generation results
 */
export function useGenerationResults(requestId: string | null) {
  return useQuery({
    queryKey: ['generation-results', requestId],
    queryFn: async () => {
      if (!requestId) throw new Error('No request ID')

      const { data } = await api.get<GenerationResultsOut>(
        `/generations/${requestId}/results`
      )
      return data
    },
    enabled: !!requestId,
  })
}

/**
 * Refresh generation status
 */
export function useRefreshGeneration() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (requestId: string) => {
      const { data } = await api.post<GenerationRequestOut>(
        `/generations/${requestId}/refresh`
      )
      return data
    },
    onSuccess: (_, requestId) => {
      queryClient.invalidateQueries({ queryKey: ['generation', requestId] })
      queryClient.invalidateQueries({ queryKey: ['generation-results', requestId] })
    },
  })
}
