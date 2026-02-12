import { api } from './client';

// --- Types ---

export interface ModelPrice {
  id: number;
  model_id: number;
  currency: string;
  unit_price: number;
  is_active: boolean;
}

export interface ModelCatalog {
  id: number;
  key: string;
  name: string;
  provider: string;
  supports_text_to_image: boolean;
  supports_image_to_image: boolean;
  supports_reference: boolean;
  supports_aspect_ratio: boolean;
  supports_style: boolean;
  is_active: boolean;
  created_at: string;
  prices: ModelPrice[];
}

export interface UpdateModelData {
  is_active?: boolean;
  name?: string;
}

export interface UpdateModelPriceData {
  unit_price: number;
}

// --- API functions ---

export const modelsApi = {
  getModels: () => api.get<ModelCatalog[]>('/admin/models'),

  updateModel: (modelId: number, data: UpdateModelData) =>
    api.patch<void>(`/admin/models/${modelId}`, data),

  updateModelPrice: (modelId: number, data: UpdateModelPriceData) =>
    api.put<void>(`/admin/models/${modelId}/price`, data),
};
