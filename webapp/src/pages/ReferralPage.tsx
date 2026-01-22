import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Gift, Copy, Check, Share2, Users, Coins, Percent } from 'lucide-react'
import { PageHeader } from '@/shared/components/layout/PageHeader'
import { GlassCard, GlassButton } from '@/shared/components/ui'
import { useReferralInfo } from '@/shared/api/hooks'
import { useHaptic } from '@/telegram/hooks'
import { openTelegramLink } from '@/telegram/sdk'

export default function ReferralPage() {
  const { t } = useTranslation()
  const { impact, notification } = useHaptic()

  const { data: referralInfo, isLoading } = useReferralInfo()
  const [copied, setCopied] = useState(false)

  const botUsername = 'bananapicsbot' // TODO: Get from config
  const referralLink = referralInfo
    ? `https://t.me/${botUsername}?start=ref_${referralInfo.referral_code}`
    : ''

  const handleCopyCode = async () => {
    if (!referralInfo?.referral_code) return

    try {
      await navigator.clipboard.writeText(referralInfo.referral_code)
      setCopied(true)
      notification('success')
      setTimeout(() => setCopied(false), 2000)
    } catch {
      notification('error')
    }
  }

  const handleShare = () => {
    impact('medium')
    if (!referralLink) return

    const text = encodeURIComponent(
      'Check out BananaPics - AI Image Generation! Use my referral link to get bonus credits:'
    )
    openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(referralLink)}&text=${text}`)
  }

  return (
    <div className="page-container">
      <PageHeader title={t('referral.title')} showBack />

      {/* Header Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-4"
      >
        <GlassCard variant="elevated" gradient className="text-center py-8">
          <div className="relative inline-block">
            <div className="absolute inset-0 bg-gradient-accent rounded-full blur-2xl opacity-30" />
            <div className="relative w-20 h-20 rounded-full bg-gradient-accent flex items-center justify-center">
              <Gift className="w-10 h-10 text-white" />
            </div>
          </div>

          <h2 className="mt-4 text-xl font-bold text-tg-text">
            {t('referral.title')}
          </h2>
          <p className="mt-2 text-sm text-tg-hint max-w-[250px] mx-auto">
            Invite friends and earn bonus credits on their purchases!
          </p>
        </GlassCard>
      </motion.div>

      {/* Referral Code */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mt-6"
      >
        <h2 className="section-title">{t('referral.yourCode')}</h2>
        <GlassCard>
          <div className="flex items-center gap-3">
            <div className="flex-1 bg-white/5 rounded-xl px-4 py-3 font-mono text-lg text-tg-text">
              {isLoading ? '...' : referralInfo?.referral_code}
            </div>
            <GlassButton
              variant="secondary"
              onClick={handleCopyCode}
            >
              {copied ? (
                <Check className="w-5 h-5" />
              ) : (
                <Copy className="w-5 h-5" />
              )}
            </GlassButton>
          </div>

          <GlassButton
            variant="primary"
            fullWidth
            className="mt-4"
            onClick={handleShare}
          >
            <Share2 className="w-5 h-5" />
            {t('referral.share')}
          </GlassButton>
        </GlassCard>
      </motion.section>

      {/* Statistics */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mt-6"
      >
        <h2 className="section-title">{t('referral.stats')}</h2>
        <div className="grid grid-cols-3 gap-3">
          <GlassCard className="text-center">
            <div className="w-10 h-10 mx-auto rounded-xl bg-blue-500/20 flex items-center justify-center">
              <Users className="w-5 h-5 text-blue-500" />
            </div>
            <p className="mt-3 text-2xl font-bold text-tg-text">
              {referralInfo?.referrals_count ?? 0}
            </p>
            <p className="text-xs text-tg-hint">{t('referral.invited')}</p>
          </GlassCard>

          <GlassCard className="text-center">
            <div className="w-10 h-10 mx-auto rounded-xl bg-green-500/20 flex items-center justify-center">
              <Coins className="w-5 h-5 text-green-500" />
            </div>
            <p className="mt-3 text-2xl font-bold gradient-text">
              {referralInfo?.referral_credits_total ?? 0}
            </p>
            <p className="text-xs text-tg-hint">{t('referral.earned')}</p>
          </GlassCard>

          <GlassCard className="text-center">
            <div className="w-10 h-10 mx-auto rounded-xl bg-purple-500/20 flex items-center justify-center">
              <Percent className="w-5 h-5 text-purple-500" />
            </div>
            <p className="mt-3 text-2xl font-bold text-tg-text">
              +{referralInfo?.bonus_percent ?? 0}%
            </p>
            <p className="text-xs text-tg-hint">{t('referral.bonus')}</p>
          </GlassCard>
        </div>
      </motion.section>
    </div>
  )
}
