// API Response types matching backend schemas

// User types
export interface UserSyncIn {
  telegram_id: number
  referral_code?: string
}

export interface UserSyncOut {
  id: number
  telegram_id: number
  created_at: string
  referral_code: string
  referral_applied: boolean
  referrer_telegram_id?: number
  bonus_percent: number
}

export interface BalanceOut {
  user_id: number
  balance: number
}

export interface TrialStatusOut {
  user_id: number
  trial_available: boolean
  used_count: number
}

// Model types
export interface ModelOptionsOut {
  supports_size: boolean
  supports_aspect_ratio: boolean
  supports_resolution: boolean
  supports_quality: boolean
  supports_input_fidelity: boolean
  quality_stars?: number
  avg_duration_seconds_min?: number
  avg_duration_seconds_max?: number
  size_options?: string[]
  aspect_ratio_options?: string[]
  resolution_options?: string[]
  quality_options?: string[]
  input_fidelity_options?: string[]
}

export interface ModelCatalogOut {
  id: number
  key: string
  name: string
  provider: string
  supports_text_to_image: boolean
  supports_image_to_image: boolean
  supports_reference: boolean
  supports_aspect_ratio: boolean
  supports_style: boolean
  is_active: boolean
  created_at: string
  options: ModelOptionsOut
}

export interface GenerationPriceOut {
  model_id: number
  model_key: string
  price_credits: number
  price_usd: number
  is_dynamic: boolean
  cached: boolean
}

export interface ModelCatalogWithPricesOut {
  model: ModelCatalogOut
  prices: GenerationPriceOut[]
}

// Generation types
export interface GenerationSubmitIn {
  telegram_id: number
  model_id: number
  prompt: string
  size?: string
  aspect_ratio?: string
  resolution?: string
  quality?: string
  input_fidelity?: string
  language?: string
  reference_urls?: string[]
  reference_file_ids?: string[]
  chat_id?: number
  message_id?: number
  prompt_message_id?: number
}

export interface GenerationRequestOut {
  id: number
  public_id: string
  user_id: number
  model_id: number
  prompt: string
  status: 'pending' | 'configuring' | 'queued' | 'running' | 'completed' | 'failed'
  size?: string
  input_params?: Record<string, unknown>
  aspect_ratio?: string
  style?: string
  error_message?: string
  references_count: number
  cost: number
  created_at: string
  updated_at: string
  started_at?: string
  completed_at?: string
}

export interface GenerationSubmitOut {
  request: GenerationRequestOut
  job_id: number
  provider_job_id?: string
  trial_used: boolean
}

export interface GenerationActiveOut {
  has_active: boolean
  request_id?: number
  public_id?: string
  status?: string
}

export interface GenerationResultOut {
  id: number
  request_id: number
  image_url: string
  seed?: number
  duration_ms?: number
  created_at: string
}

export interface GenerationResultsOut {
  request: GenerationRequestOut
  results: GenerationResultOut[]
}

// Payment types
export interface StarsPaymentOptionsOut {
  enabled: boolean
  min_stars: number
  preset_stars: number[]
  exchange_numerator: number
  exchange_denominator: number
  currency: string
}

export interface StarsPaymentConfirmIn {
  telegram_id: number
  stars_amount: number
  currency: string
  telegram_charge_id: string
  provider_charge_id: string
  invoice_payload: string
}

export interface StarsPaymentConfirmOut {
  credits_added: number
  balance: number
}

// Referral types
export interface ReferralInfoOut {
  user_id: number
  referral_code: string
  referrals_count: number
  referral_credits_total: number
  bonus_percent: number
}

// Size options
export interface SizeOptionOut {
  key: string
  label: string
  width: number
  height: number
}

// Price calculation
export interface PriceCalculateIn {
  telegram_id: number
  model_id: number
  size?: string
  aspect_ratio?: string
  resolution?: string
  quality?: string
  input_fidelity?: string
  references_count?: number
}

export interface PriceCalculateOut {
  model_id: number
  price_credits: number
  price_usd: number
  has_balance: boolean
  trial_available: boolean
}
