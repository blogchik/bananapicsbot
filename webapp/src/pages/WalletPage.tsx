import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Wallet, Star, Check } from 'lucide-react'
import { PageHeader } from '@/shared/components/layout/PageHeader'
import { GlassCard, GlassButton, GlassInput } from '@/shared/components/ui'
import { useBalance, usePaymentOptions } from '@/shared/api/hooks'
import { useHaptic } from '@/telegram/hooks'
import { cn } from '@/shared/lib/cn'

export default function WalletPage() {
  const { t } = useTranslation()
  const { impact, notification } = useHaptic()

  const { data: balanceData } = useBalance()
  const { data: paymentOptions } = usePaymentOptions()

  const [selectedAmount, setSelectedAmount] = useState<number | null>(null)
  const [customAmount, setCustomAmount] = useState('')

  const presetAmounts = paymentOptions?.preset_stars || [50, 100, 250, 500, 1000]

  const calculateCredits = (stars: number) => {
    if (!paymentOptions) return 0
    return Math.floor(
      (stars * paymentOptions.exchange_numerator) / paymentOptions.exchange_denominator
    )
  }

  const handleSelectAmount = (amount: number) => {
    impact('light')
    setSelectedAmount(amount)
    setCustomAmount('')
  }

  const handleCustomAmountChange = (value: string) => {
    const num = parseInt(value, 10)
    if (value === '' || (!isNaN(num) && num >= 0)) {
      setCustomAmount(value)
      setSelectedAmount(null)
    }
  }

  const handlePayment = () => {
    impact('medium')
    const amount = selectedAmount || parseInt(customAmount, 10)
    if (!amount) return

    // TODO: Implement Telegram Stars payment
    notification('success')
  }

  const currentAmount = selectedAmount || parseInt(customAmount, 10) || 0
  const creditsToReceive = calculateCredits(currentAmount)

  return (
    <div className="page-container">
      <PageHeader title={t('wallet.title')} />

      {/* Balance Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-4"
      >
        <GlassCard variant="elevated" gradient>
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-accent flex items-center justify-center">
              <Wallet className="w-7 h-7 text-white" />
            </div>
            <div>
              <p className="text-sm text-tg-hint">{t('wallet.balance')}</p>
              <p className="text-3xl font-bold gradient-text">
                {balanceData?.balance?.toLocaleString() ?? 0}
              </p>
            </div>
          </div>
        </GlassCard>
      </motion.div>

      {/* Top Up Section */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mt-6"
      >
        <h2 className="section-title">{t('wallet.selectAmount')}</h2>

        {/* Preset amounts */}
        <div className="grid grid-cols-3 gap-3">
          {presetAmounts.map((amount) => (
            <GlassCard
              key={amount}
              className={cn(
                'cursor-pointer text-center transition-all',
                selectedAmount === amount && 'ring-2 ring-accent-purple'
              )}
              onClick={() => handleSelectAmount(amount)}
            >
              <div className="flex items-center justify-center gap-1">
                <Star className="w-4 h-4 text-yellow-500" />
                <span className="font-bold text-tg-text">{amount}</span>
              </div>
              <p className="text-xs text-tg-hint mt-1">
                {calculateCredits(amount)} cr
              </p>
              {selectedAmount === amount && (
                <div className="absolute top-2 right-2">
                  <Check className="w-4 h-4 text-accent-purple" />
                </div>
              )}
            </GlassCard>
          ))}
        </div>

        {/* Custom amount */}
        <div className="mt-4">
          <GlassInput
            label={t('wallet.customAmount')}
            type="number"
            value={customAmount}
            onChange={(e) => handleCustomAmountChange(e.target.value)}
            placeholder="Enter stars amount"
          />
        </div>

        {/* Credits preview */}
        {currentAmount > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-4"
          >
            <GlassCard className="flex items-center justify-between">
              <span className="text-tg-hint">{t('wallet.youGet')}</span>
              <div className="flex items-center gap-2">
                <span className="text-2xl font-bold gradient-text">
                  {creditsToReceive.toLocaleString()}
                </span>
                <span className="text-sm text-tg-hint">{t('common.credits')}</span>
              </div>
            </GlassCard>
          </motion.div>
        )}

        {/* Pay button */}
        <GlassButton
          variant="primary"
          size="lg"
          fullWidth
          className="mt-6"
          disabled={currentAmount <= 0}
          onClick={handlePayment}
        >
          <Star className="w-5 h-5" />
          {t('wallet.pay')} {currentAmount > 0 && `${currentAmount} ${t('common.stars')}`}
        </GlassButton>
      </motion.section>
    </div>
  )
}
