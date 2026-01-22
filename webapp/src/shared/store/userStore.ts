import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface UserState {
  // User data
  telegramId: number | null
  balance: number
  trialAvailable: boolean
  referralCode: string
  referralsCount: number
  referralCreditsTotal: number
  bonusPercent: number

  // Settings
  language: 'uz' | 'ru' | 'en'

  // Actions
  setTelegramId: (id: number) => void
  setBalance: (balance: number) => void
  setTrialAvailable: (available: boolean) => void
  setReferralInfo: (info: {
    referralCode: string
    referralsCount: number
    referralCreditsTotal: number
    bonusPercent: number
  }) => void
  setLanguage: (lang: 'uz' | 'ru' | 'en') => void
  reset: () => void
}

const initialState = {
  telegramId: null,
  balance: 0,
  trialAvailable: false,
  referralCode: '',
  referralsCount: 0,
  referralCreditsTotal: 0,
  bonusPercent: 0,
  language: 'uz' as const,
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      ...initialState,

      setTelegramId: (telegramId) => set({ telegramId }),

      setBalance: (balance) => set({ balance }),

      setTrialAvailable: (trialAvailable) => set({ trialAvailable }),

      setReferralInfo: (info) =>
        set({
          referralCode: info.referralCode,
          referralsCount: info.referralsCount,
          referralCreditsTotal: info.referralCreditsTotal,
          bonusPercent: info.bonusPercent,
        }),

      setLanguage: (language) => set({ language }),

      reset: () => set(initialState),
    }),
    {
      name: 'bananapics-user',
      partialize: (state) => ({
        language: state.language,
      }),
    }
  )
)
