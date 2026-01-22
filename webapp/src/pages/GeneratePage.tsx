import { useEffect, useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Sparkles,
  ChevronRight,
  Loader2,
  Check,
  AlertCircle,
} from 'lucide-react'
import { PageHeader } from '@/shared/components/layout/PageHeader'
import {
  GlassCard,
  GlassButton,
  GlassTextarea,
  Badge,
  PageLoader,
} from '@/shared/components/ui'
import {
  useModels,
  useCalculatePrice,
  useSubmitGeneration,
  useActiveGeneration,
  useBalance,
  useTrialStatus,
} from '@/shared/api/hooks'
import { useGenerationStore, useUserStore } from '@/shared/store'
import type { GenerationOptions } from '@/shared/store/generationStore'
import { useMainButton, useHaptic } from '@/telegram/hooks'
import type { ModelCatalogWithPricesOut } from '@/shared/types/api'

export default function GeneratePage() {
  const { t } = useTranslation()
  const { impact, notification } = useHaptic()

  // Store state
  const {
    selectedModel,
    setSelectedModel,
    prompt,
    setPrompt,
    options,
    setOption,
    calculatedPrice,
    canAfford,
    activeGeneration,
    resetForm,
  } = useGenerationStore()

  const balance = useUserStore((s) => s.balance)
  const trialAvailable = useUserStore((s) => s.trialAvailable)

  // API hooks
  const { data: models, isLoading: modelsLoading } = useModels()
  const { mutate: calculatePrice, isPending: priceLoading } = useCalculatePrice()
  const { mutate: submitGeneration, isPending: submitting } = useSubmitGeneration()
  useActiveGeneration()
  useBalance()
  useTrialStatus()

  // Local state
  const [showModelSelector, setShowModelSelector] = useState(true)

  // Calculate price when model or options change
  useEffect(() => {
    if (selectedModel) {
      calculatePrice({
        model_id: selectedModel.model.id,
        size: options.size,
        aspect_ratio: options.aspectRatio,
        resolution: options.resolution,
        quality: options.quality,
        input_fidelity: options.inputFidelity,
      })
    }
  }, [selectedModel, options, calculatePrice])

  // Handle generation submit
  const handleSubmit = useCallback(() => {
    if (!selectedModel || !prompt.trim()) return

    impact('medium')
    submitGeneration(
      {
        model_id: selectedModel.model.id,
        prompt: prompt.trim(),
        size: options.size,
        aspect_ratio: options.aspectRatio,
        resolution: options.resolution,
        quality: options.quality,
        input_fidelity: options.inputFidelity,
      },
      {
        onSuccess: () => {
          notification('success')
          resetForm()
        },
        onError: () => {
          notification('error')
        },
      }
    )
  }, [
    selectedModel,
    prompt,
    options,
    impact,
    submitGeneration,
    notification,
    resetForm,
  ])

  // Main button logic
  const canSubmit =
    selectedModel &&
    prompt.trim().length >= 3 &&
    (canAfford || !!trialAvailable) &&
    !submitting &&
    !activeGeneration?.status

  const buttonText = submitting
    ? t('generate.generating')
    : trialAvailable
    ? t('generate.useFreeTrial')
    : `${t('generate.generate')} • ${calculatedPrice} ${t('common.credits')}`

  useMainButton(
    showModelSelector ? '' : buttonText,
    handleSubmit,
    !!canSubmit
  )

  // Model selection
  const handleSelectModel = (model: ModelCatalogWithPricesOut) => {
    impact('light')
    setSelectedModel(model)
    setShowModelSelector(false)
  }

  if (modelsLoading) {
    return <PageLoader text={t('common.loading')} />
  }

  // Show active generation status
  if (activeGeneration && activeGeneration.status !== 'completed' && activeGeneration.status !== 'failed') {
    return (
      <div className="page-container">
        <PageHeader title={t('generate.title')} showBack />
        <GenerationProgress status={activeGeneration.status} />
      </div>
    )
  }

  return (
    <div className="page-container">
      <PageHeader title={t('generate.title')} showBack={!showModelSelector} />

      <AnimatePresence mode="wait">
        {showModelSelector ? (
          <ModelSelector
            key="model-selector"
            models={models || []}
            onSelect={handleSelectModel}
          />
        ) : (
          <GenerationForm
            key="generation-form"
            model={selectedModel!}
            prompt={prompt}
            onPromptChange={setPrompt}
            options={options}
            onOptionChange={setOption}
            price={calculatedPrice}
            priceLoading={priceLoading}
            canAfford={canAfford}
            trialAvailable={trialAvailable}
            balance={balance}
            onBack={() => setShowModelSelector(true)}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

// Model Selector Component
function ModelSelector({
  models,
  onSelect,
}: {
  models: ModelCatalogWithPricesOut[]
  onSelect: (model: ModelCatalogWithPricesOut) => void
}) {
  const { t } = useTranslation()

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="mt-4 space-y-3"
    >
      <h2 className="section-title">{t('generate.selectModel')}</h2>

      {models.map((item, index) => (
        <motion.div
          key={item.model.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.05 }}
        >
          <GlassCard
            className="cursor-pointer group"
            onClick={() => onSelect(item)}
          >
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-accent flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>

              <div className="flex-1 min-w-0">
                <h3 className="font-medium text-tg-text truncate">
                  {item.model.name}
                </h3>
                <div className="flex items-center gap-2 mt-1">
                  {item.model.supports_text_to_image && (
                    <Badge size="sm">T2I</Badge>
                  )}
                  {item.model.supports_image_to_image && (
                    <Badge size="sm">I2I</Badge>
                  )}
                  {item.model.options.quality_stars && (
                    <span className="text-xs text-tg-hint">
                      {'★'.repeat(item.model.options.quality_stars)}
                    </span>
                  )}
                </div>
              </div>

              <div className="text-right">
                <p className="text-sm font-medium gradient-text">
                  {item.prices[0]?.price_credits ?? '?'}
                </p>
                <p className="text-xs text-tg-hint">{t('common.credits')}</p>
              </div>

              <ChevronRight className="w-5 h-5 text-tg-hint group-hover:text-tg-text transition-colors" />
            </div>
          </GlassCard>
        </motion.div>
      ))}
    </motion.div>
  )
}

// Generation Form Component
function GenerationForm({
  model,
  prompt,
  onPromptChange,
  options,
  onOptionChange,
  price,
  priceLoading,
  canAfford,
  trialAvailable,
  balance,
  onBack,
}: {
  model: ModelCatalogWithPricesOut
  prompt: string
  onPromptChange: (value: string) => void
  options: GenerationOptions
  onOptionChange: <K extends keyof GenerationOptions>(key: K, value: GenerationOptions[K]) => void
  price: number
  priceLoading: boolean
  canAfford: boolean
  trialAvailable: boolean | null
  balance: number
  onBack: () => void
}) {
  const { t } = useTranslation()
  const { impact } = useHaptic()

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="mt-4 space-y-4"
    >
      {/* Selected Model */}
      <GlassCard
        className="cursor-pointer"
        onClick={() => {
          impact('light')
          onBack()
        }}
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-accent flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <p className="text-xs text-tg-hint">{t('generate.selectModel')}</p>
            <p className="font-medium text-tg-text">{model.model.name}</p>
          </div>
          <ChevronRight className="w-5 h-5 text-tg-hint" />
        </div>
      </GlassCard>

      {/* Prompt Input */}
      <GlassCard padding="sm">
        <GlassTextarea
          placeholder={t('generate.promptPlaceholder')}
          value={prompt}
          onChange={(e) => onPromptChange(e.target.value)}
          rows={4}
          className="bg-transparent border-0 focus:ring-0 p-0"
        />
      </GlassCard>

      {/* Options */}
      {model.model.options && (
        <div className="space-y-3">
          <h3 className="section-title">{t('generate.options')}</h3>

          {/* Aspect Ratio */}
          {model.model.options.supports_aspect_ratio &&
            model.model.options.aspect_ratio_options && (
              <OptionSelector
                label={t('generate.aspectRatio')}
                options={model.model.options.aspect_ratio_options}
                value={options.aspectRatio}
                onChange={(v) => onOptionChange('aspectRatio', v)}
              />
            )}

          {/* Quality */}
          {model.model.options.supports_quality &&
            model.model.options.quality_options && (
              <OptionSelector
                label={t('generate.quality')}
                options={model.model.options.quality_options}
                value={options.quality}
                onChange={(v) => onOptionChange('quality', v)}
              />
            )}

          {/* Resolution */}
          {model.model.options.supports_resolution &&
            model.model.options.resolution_options && (
              <OptionSelector
                label={t('generate.resolution')}
                options={model.model.options.resolution_options}
                value={options.resolution}
                onChange={(v) => onOptionChange('resolution', v)}
              />
            )}
        </div>
      )}

      {/* Price Display */}
      <GlassCard>
        <div className="flex items-center justify-between">
          <span className="text-tg-hint">{t('generate.price')}</span>
          <div className="flex items-center gap-2">
            {priceLoading ? (
              <Loader2 className="w-4 h-4 animate-spin text-tg-hint" />
            ) : (
              <>
                <span className="text-xl font-bold gradient-text">{price}</span>
                <span className="text-sm text-tg-hint">{t('common.credits')}</span>
              </>
            )}
          </div>
        </div>

        {/* Balance warning */}
        {!canAfford && !trialAvailable && (
          <div className="mt-3 p-2 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-500" />
            <span className="text-sm text-red-500">
              {t('generate.insufficientBalance')} (Balance: {balance})
            </span>
          </div>
        )}

        {/* Trial available */}
        {trialAvailable && (
          <div className="mt-3 p-2 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center gap-2">
            <Check className="w-4 h-4 text-green-500" />
            <span className="text-sm text-green-500">
              {t('generate.useFreeTrial')}
            </span>
          </div>
        )}
      </GlassCard>
    </motion.div>
  )
}

// Option Selector Component
function OptionSelector({
  label,
  options,
  value,
  onChange,
}: {
  label: string
  options: string[]
  value?: string
  onChange: (value: string) => void
}) {
  const { impact } = useHaptic()

  return (
    <div>
      <p className="text-sm text-tg-hint mb-2">{label}</p>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <GlassButton
            key={option}
            variant={value === option ? 'primary' : 'default'}
            size="sm"
            onClick={() => {
              impact('light')
              onChange(option)
            }}
          >
            {option}
          </GlassButton>
        ))}
      </div>
    </div>
  )
}

// Generation Progress Component
function GenerationProgress({ status }: { status: string }) {
  const { t } = useTranslation()

  const statusMessages: Record<string, string> = {
    pending: 'Starting...',
    configuring: 'Configuring...',
    queued: 'In queue...',
    running: 'Generating...',
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="mt-8"
    >
      <GlassCard variant="elevated" className="text-center py-12">
        <div className="relative inline-block">
          <div className="absolute inset-0 bg-gradient-accent rounded-full blur-2xl opacity-30 animate-pulse-slow" />
          <div className="relative w-20 h-20 mx-auto border-4 border-white/10 border-t-accent-purple rounded-full animate-spin" />
        </div>

        <p className="mt-6 text-lg font-medium text-tg-text">
          {statusMessages[status] || t('generate.generating')}
        </p>
        <p className="mt-2 text-sm text-tg-hint">
          Please wait...
        </p>
      </GlassCard>
    </motion.div>
  )
}
