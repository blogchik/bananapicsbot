import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Images, Sparkles } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '@/shared/components/layout/PageHeader'
import { GlassCard, GlassButton } from '@/shared/components/ui'

export default function GalleryPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()

  // TODO: Implement gallery with useInfiniteQuery

  return (
    <div className="page-container">
      <PageHeader title={t('gallery.title')} />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-8"
      >
        <GlassCard className="text-center py-12">
          <div className="w-16 h-16 mx-auto rounded-full bg-white/10 flex items-center justify-center mb-4">
            <Images className="w-8 h-8 text-tg-hint" />
          </div>
          <h3 className="text-lg font-medium text-tg-text">
            {t('gallery.empty')}
          </h3>
          <p className="mt-2 text-sm text-tg-hint">
            {t('gallery.emptyHint')}
          </p>
          <GlassButton
            variant="primary"
            className="mt-6"
            onClick={() => navigate('/generate')}
          >
            <Sparkles className="w-4 h-4" />
            {t('home.generateImage')}
          </GlassButton>
        </GlassCard>
      </motion.div>
    </div>
  )
}
