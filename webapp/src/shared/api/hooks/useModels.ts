import { useQuery } from '@tanstack/react-query'
import { api } from '../client'
import type { ModelCatalogWithPricesOut, SizeOptionOut } from '@/shared/types/api'

/**
 * Get all available models with prices
 */
export function useModels() {
  return useQuery({
    queryKey: ['models'],
    queryFn: async () => {
      const { data } = await api.get<ModelCatalogWithPricesOut[]>('/models')
      return data
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

/**
 * Get model by ID
 */
export function useModel(modelId: number | null) {
  const { data: models } = useModels()

  return models?.find((m) => m.model.id === modelId) ?? null
}

/**
 * Get available size options
 */
export function useSizeOptions() {
  return useQuery({
    queryKey: ['sizes'],
    queryFn: async () => {
      const { data } = await api.get<SizeOptionOut[]>('/sizes')
      return data
    },
    staleTime: 30 * 60 * 1000, // 30 minutes
  })
}

/**
 * Filter models by capability
 */
export function useModelsByCapability(
  capability: 'text_to_image' | 'image_to_image' | 'reference'
) {
  const { data: models, ...rest } = useModels()

  const filteredModels = models?.filter((m) => {
    switch (capability) {
      case 'text_to_image':
        return m.model.supports_text_to_image
      case 'image_to_image':
        return m.model.supports_image_to_image
      case 'reference':
        return m.model.supports_reference
      default:
        return true
    }
  })

  return { data: filteredModels, ...rest }
}
