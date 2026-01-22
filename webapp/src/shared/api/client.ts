import axios, { type AxiosInstance, type AxiosError } from 'axios'
import { getInitData } from '@/telegram/sdk'

// API base URL - defaults to same origin in production
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

/**
 * Create configured axios instance
 */
function createApiClient(): AxiosInstance {
  const instance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // Request interceptor - add init data
  instance.interceptors.request.use(
    (config) => {
      const initData = getInitData()
      if (initData) {
        config.headers['X-Telegram-Init-Data'] = initData
      }
      return config
    },
    (error) => Promise.reject(error)
  )

  // Response interceptor - handle errors
  instance.interceptors.response.use(
    (response) => response,
    (error: AxiosError<ApiError>) => {
      // Extract error details
      const apiError: ApiErrorResponse = {
        message: 'An unexpected error occurred',
        code: 'UNKNOWN_ERROR',
        status: error.response?.status ?? 500,
      }

      if (error.response?.data) {
        apiError.message = error.response.data.detail || error.response.data.message || apiError.message
        apiError.code = error.response.data.code || apiError.code
      } else if (error.message === 'Network Error') {
        apiError.message = 'Network error. Please check your connection.'
        apiError.code = 'NETWORK_ERROR'
      } else if (error.code === 'ECONNABORTED') {
        apiError.message = 'Request timed out. Please try again.'
        apiError.code = 'TIMEOUT'
      }

      return Promise.reject(apiError)
    }
  )

  return instance
}

// API error types
interface ApiError {
  detail?: string
  message?: string
  code?: string
}

export interface ApiErrorResponse {
  message: string
  code: string
  status: number
}

// Singleton instance
export const api = createApiClient()

// Helper function to check if error is API error
export function isApiError(error: unknown): error is ApiErrorResponse {
  return (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    'code' in error &&
    'status' in error
  )
}
