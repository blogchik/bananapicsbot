import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import {
  Sparkles,
  Images,
  Wrench,
  Wallet,
  Gift,
  Copy,
  Check,
  ChevronRight,
  Zap,
} from 'lucide-react'
import { PageHeader } from '@/shared/components/layout/PageHeader'
import { GlassCard, GlassButton, Badge, Avatar } from '@/shared/components/ui'
import { useTelegramContext } from '@/app/providers'
import {
  useBalance,
  useTrialStatus,
  useReferralInfo,
  useSyncUser,
} from '@/shared/api/hooks'
import { useHaptic } from '@/telegram/hooks'
import { cn } from '@/shared/lib/cn'
import { getStartParam } from '@/telegram/sdk'

export default function HomePage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { user } = useTelegramContext()
  const { impact, notification } = useHaptic()

  const [copied, setCopied] = useState(false)

  // Sync user on mount
  const { mutate: syncUser } = useSyncUser()
  useEffect(() => {
    const startParam = getStartParam()
    // Extract referral code from start param if present
    const referralCode = startParam?.startsWith('ref_') ? startParam : undefined
    syncUser(referralCode)
  }, [syncUser])

  // Fetch user data
  const { data: balanceData, isLoading: balanceLoading } = useBalance()
  const { data: trialData } = useTrialStatus()
  const { data: referralData } = useReferralInfo()

  const handleCopyReferral = async () => {
    if (!referralData?.referral_code) return

    try {
      await navigator.clipboard.writeText(referralData.referral_code)
      setCopied(true)
      notification('success')
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for older browsers
      notification('error')
    }
  }

  const quickActions = [
    {
      icon: Sparkles,
      label: t('home.generateImage'),
      path: '/generate',
      gradient: 'from-purple-500 to-blue-500',
    },
    {
      icon: Images,
      label: t('home.viewGallery'),
      path: '/gallery',
      gradient: 'from-blue-500 to-cyan-500',
    },
    {
      icon: Wrench,
      label: t('home.imageTools'),
      path: '/tools',
      gradient: 'from-cyan-500 to-green-500',
    },
    {
      icon: Wallet,
      label: t('home.topUp'),
      path: '/wallet',
      gradient: 'from-green-500 to-yellow-500',
    },
  ]

  return (
    <div className="page-container">
      <PageHeader
        title={t('home.welcome', { name: user?.first_name || 'User' })}
      />

      {/* User Avatar & Balance Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="mt-4"
      >
        <GlassCard variant="elevated" gradient className="relative overflow-visible">
          {/* Decorative glow */}
          <div className="absolute -top-10 -right-10 w-32 h-32 bg-accent-purple/30 rounded-full blur-3xl" />
          <div className="absolute -bottom-10 -left-10 w-32 h-32 bg-accent-blue/30 rounded-full blur-3xl" />

          <div className="relative flex items-center gap-4">
            <Avatar
              src={user?.photo_url}
              name={user?.first_name || 'U'}
              size="xl"
            />

            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm text-tg-hint">{t('home.balance')}</span>
                {user?.is_premium && (
                  <Badge variant="premium" size="sm">Premium</Badge>
                )}
              </div>
              <div className="flex items-baseline gap-1 mt-1">
                {balanceLoading ? (
                  <div className="h-8 w-24 bg-white/10 rounded animate-pulse" />
                ) : (
                  <>
                    <span className="text-3xl font-bold gradient-text">
                      {balanceData?.balance?.toLocaleString() ?? 0}
                    </span>
                    <span className="text-sm text-tg-hint">{t('common.credits')}</span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Trial Badge */}
          {trialData?.trial_available && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="mt-4 p-3 rounded-xl bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/30"
            >
              <div className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-green-500" />
                <span className="text-sm font-medium text-green-500">
                  {t('home.trialAvailable')}
                </span>
              </div>
            </motion.div>
          )}
        </GlassCard>
      </motion.div>

      {/* Quick Actions */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
        className="mt-6"
      >
        <h2 className="section-title">{t('home.quickActions')}</h2>
        <div className="grid grid-cols-2 gap-3">
          {quickActions.map((action, index) => (
            <motion.div
              key={action.path}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.2, delay: 0.1 + index * 0.05 }}
            >
              <GlassCard
                className="cursor-pointer group"
                onClick={() => {
                  impact('light')
                  navigate(action.path)
                }}
              >
                <div
                  className={cn(
                    'w-10 h-10 rounded-xl flex items-center justify-center',
                    'bg-gradient-to-br',
                    action.gradient,
                    'group-hover:scale-110 transition-transform'
                  )}
                >
                  <action.icon className="w-5 h-5 text-white" />
                </div>
                <span className="mt-3 block text-sm font-medium text-tg-text">
                  {action.label}
                </span>
                <ChevronRight className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tg-hint opacity-0 group-hover:opacity-100 transition-opacity" />
              </GlassCard>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* Referral Section */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.2 }}
        className="mt-6"
      >
        <h2 className="section-title">{t('home.referral')}</h2>
        <GlassCard>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-pink-500 flex items-center justify-center">
              <Gift className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1">
              <p className="text-sm text-tg-hint">{t('home.referralCode')}</p>
              <p className="font-mono font-medium text-tg-text">
                {referralData?.referral_code || '...'}
              </p>
            </div>
            <GlassButton
              variant="secondary"
              size="sm"
              onClick={handleCopyReferral}
            >
              {copied ? (
                <Check className="w-4 h-4" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
              <span className="ml-1">
                {copied ? t('home.copied') : t('home.copyCode')}
              </span>
            </GlassButton>
          </div>

          {/* Referral Stats */}
          {referralData && referralData.referrals_count > 0 && (
            <div className="mt-4 pt-4 border-t border-white/10 grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-tg-text">
                  {referralData.referrals_count}
                </p>
                <p className="text-xs text-tg-hint">{t('referral.invited')}</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold gradient-text">
                  {referralData.referral_credits_total}
                </p>
                <p className="text-xs text-tg-hint">{t('referral.earned')}</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-500">
                  +{referralData.bonus_percent}%
                </p>
                <p className="text-xs text-tg-hint">{t('referral.bonus')}</p>
              </div>
            </div>
          )}
        </GlassCard>
      </motion.section>
    </div>
  )
}
