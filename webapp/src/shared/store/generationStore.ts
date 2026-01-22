import { create } from 'zustand'
import type { ModelCatalogWithPricesOut } from '@/shared/types/api'

export interface GenerationOptions {
  size?: string
  aspectRatio?: string
  resolution?: string
  quality?: string
  inputFidelity?: string
}

interface ActiveGeneration {
  requestId: number
  publicId: string
  status: string
}

interface GenerationState {
  // Model selection
  selectedModel: ModelCatalogWithPricesOut | null

  // Generation parameters
  prompt: string
  referenceImages: string[]
  options: GenerationOptions

  // Price
  calculatedPrice: number
  canAfford: boolean

  // Active generation
  activeGeneration: ActiveGeneration | null

  // Actions
  setSelectedModel: (model: ModelCatalogWithPricesOut | null) => void
  setPrompt: (prompt: string) => void
  addReferenceImage: (url: string) => void
  removeReferenceImage: (index: number) => void
  clearReferenceImages: () => void
  setOption: <K extends keyof GenerationOptions>(key: K, value: GenerationOptions[K]) => void
  setOptions: (options: GenerationOptions) => void
  setCalculatedPrice: (price: number, canAfford: boolean) => void
  setActiveGeneration: (generation: ActiveGeneration | null) => void
  reset: () => void
  resetForm: () => void
}

const initialFormState = {
  prompt: '',
  referenceImages: [],
  options: {},
  calculatedPrice: 0,
  canAfford: true,
}

const initialState = {
  ...initialFormState,
  selectedModel: null,
  activeGeneration: null,
}

export const useGenerationStore = create<GenerationState>((set) => ({
  ...initialState,

  setSelectedModel: (selectedModel) =>
    set({
      selectedModel,
      // Reset options when model changes
      options: {},
      calculatedPrice: 0,
    }),

  setPrompt: (prompt) => set({ prompt }),

  addReferenceImage: (url) =>
    set((state) => ({
      referenceImages: [...state.referenceImages, url].slice(0, 4), // Max 4 references
    })),

  removeReferenceImage: (index) =>
    set((state) => ({
      referenceImages: state.referenceImages.filter((_, i) => i !== index),
    })),

  clearReferenceImages: () => set({ referenceImages: [] }),

  setOption: (key, value) =>
    set((state) => ({
      options: { ...state.options, [key]: value },
    })),

  setOptions: (options) => set({ options }),

  setCalculatedPrice: (calculatedPrice, canAfford) =>
    set({ calculatedPrice, canAfford }),

  setActiveGeneration: (activeGeneration) => set({ activeGeneration }),

  reset: () => set(initialState),

  resetForm: () => set(initialFormState),
}))
