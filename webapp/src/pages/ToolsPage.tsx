import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import {
  Eraser,
  Maximize2,
  Waves,
  Clock,
  Wand2,
  ChevronRight,
} from 'lucide-react'
import { PageHeader } from '@/shared/components/layout/PageHeader'
import { GlassCard, Badge } from '@/shared/components/ui'
import { useHaptic } from '@/telegram/hooks'
import { cn } from '@/shared/lib/cn'

interface Tool {
  id: string
  icon: React.ComponentType<{ className?: string }>
  titleKey: string
  descKey: string
  price: number
  gradient: string
}

const tools: Tool[] = [
  {
    id: 'watermark-remove',
    icon: Eraser,
    titleKey: 'tools.watermarkRemove',
    descKey: 'tools.watermarkRemoveDesc',
    price: 12,
    gradient: 'from-red-500 to-orange-500',
  },
  {
    id: 'upscale',
    icon: Maximize2,
    titleKey: 'tools.upscale',
    descKey: 'tools.upscaleDesc',
    price: 60,
    gradient: 'from-purple-500 to-blue-500',
  },
  {
    id: 'denoise',
    icon: Waves,
    titleKey: 'tools.denoise',
    descKey: 'tools.denoiseDesc',
    price: 20,
    gradient: 'from-blue-500 to-cyan-500',
  },
  {
    id: 'restore',
    icon: Clock,
    titleKey: 'tools.restore',
    descKey: 'tools.restoreDesc',
    price: 20,
    gradient: 'from-cyan-500 to-green-500',
  },
  {
    id: 'enhance',
    icon: Wand2,
    titleKey: 'tools.enhance',
    descKey: 'tools.enhanceDesc',
    price: 30,
    gradient: 'from-green-500 to-yellow-500',
  },
]

export default function ToolsPage() {
  const { t } = useTranslation()
  const { impact } = useHaptic()

  const handleToolClick = (toolId: string) => {
    impact('light')
    // TODO: Navigate to tool page or open modal
    console.log('Tool clicked:', toolId)
  }

  return (
    <div className="page-container">
      <PageHeader title={t('tools.title')} />

      <div className="mt-4 space-y-3">
        {tools.map((tool, index) => (
          <motion.div
            key={tool.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <GlassCard
              className="cursor-pointer group"
              onClick={() => handleToolClick(tool.id)}
            >
              <div className="flex items-center gap-4">
                <div
                  className={cn(
                    'w-12 h-12 rounded-xl flex items-center justify-center',
                    'bg-gradient-to-br',
                    tool.gradient,
                    'group-hover:scale-110 transition-transform'
                  )}
                >
                  <tool.icon className="w-6 h-6 text-white" />
                </div>

                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-tg-text">
                    {t(tool.titleKey)}
                  </h3>
                  <p className="text-sm text-tg-hint truncate">
                    {t(tool.descKey)}
                  </p>
                </div>

                <div className="text-right flex-shrink-0">
                  <Badge variant="default">{tool.price} cr</Badge>
                </div>

                <ChevronRight className="w-5 h-5 text-tg-hint group-hover:text-tg-text transition-colors" />
              </div>
            </GlassCard>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
