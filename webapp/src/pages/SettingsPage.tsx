import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Globe, Check } from 'lucide-react'
import { PageHeader } from '@/shared/components/layout/PageHeader'
import { GlassCard, Badge } from '@/shared/components/ui'
import { useHaptic } from '@/telegram/hooks'
import { useUserStore } from '@/shared/store'
import { languages, changeLanguage, type LanguageCode } from '@/shared/i18n'
import { cn } from '@/shared/lib/cn'

export default function SettingsPage() {
  const { t } = useTranslation()
  const { impact } = useHaptic()

  const currentLanguage = useUserStore((s) => s.language)
  const setLanguage = useUserStore((s) => s.setLanguage)

  const handleLanguageChange = (code: LanguageCode) => {
    impact('light')
    setLanguage(code)
    changeLanguage(code)
  }

  return (
    <div className="page-container">
      <PageHeader title={t('settings.title')} showBack />

      {/* Language Selection */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-4"
      >
        <h2 className="section-title">{t('settings.language')}</h2>
        <div className="space-y-2">
          {languages.map((lang) => (
            <GlassCard
              key={lang.code}
              className={cn(
                'cursor-pointer',
                currentLanguage === lang.code && 'ring-2 ring-accent-purple'
              )}
              onClick={() => handleLanguageChange(lang.code as LanguageCode)}
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                  <Globe className="w-5 h-5 text-white" />
                </div>

                <div className="flex-1">
                  <p className="font-medium text-tg-text">{lang.nativeName}</p>
                  <p className="text-sm text-tg-hint">{lang.name}</p>
                </div>

                {currentLanguage === lang.code && (
                  <Check className="w-5 h-5 text-accent-purple" />
                )}
              </div>
            </GlassCard>
          ))}
        </div>
      </motion.section>

      {/* About Section */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mt-6"
      >
        <h2 className="section-title">{t('settings.about')}</h2>
        <GlassCard>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-accent flex items-center justify-center">
              <span className="text-2xl">🍌</span>
            </div>

            <div className="flex-1">
              <p className="font-bold text-tg-text">BananaPics</p>
              <p className="text-sm text-tg-hint">AI Image Generation</p>
            </div>

            <Badge>{t('settings.version')} 0.1.0</Badge>
          </div>

          <div className="mt-4 pt-4 border-t border-white/10">
            <p className="text-sm text-tg-hint">
              Powered by advanced AI models. Create stunning images from text descriptions.
            </p>
          </div>
        </GlassCard>
      </motion.section>
    </div>
  )
}
