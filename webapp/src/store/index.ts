import { create } from 'zustand';
import type { AppState, GenerationItem, Toast } from '../types';
import { logger } from '../services/logger';
import { api, ApiError } from '../services/api';

// Generate unique ID using crypto API
const generateId = () => crypto.randomUUID();

// Polling interval for active generations (in ms)
const POLL_INTERVAL = 3000;

// Map backend status to frontend status
function mapStatus(backendStatus: string): GenerationItem['status'] {
  switch (backendStatus.toLowerCase()) {
    case 'completed':
      return 'done';
    case 'failed':
    case 'cancelled':
      return 'error';
    case 'pending':
    case 'configuring':
    case 'queued':
    case 'running':
      return 'generating';
    default:
      return 'idle';
  }
}

// Model info type
interface ModelInfo {
  id: number;
  key: string;
  name: string;
  options: {
    supports_aspect_ratio: boolean;
    supports_resolution: boolean;
    supports_quality: boolean;
    aspect_ratio_options: string[] | null;
    resolution_options: string[] | null;
    quality_options: string[] | null;
  };
  basePrice: number;
}

// Extended state with internal fields
interface ExtendedState extends AppState {
  // Internal state
  telegramId: number | null;
  isInitialized: boolean;
  models: ModelInfo[];
  selectedModelId: number | null;
  pollingIntervalId: ReturnType<typeof setInterval> | null;
  trialAvailable: boolean;

  // Internal actions
  initialize: (telegramId: number) => Promise<void>;
  loadModels: () => Promise<void>;
  loadBalance: () => Promise<void>;
  startPolling: () => void;
  stopPolling: () => void;
  pollActiveGeneration: () => Promise<void>;
  setSelectedModel: (modelId: number) => void;
}

export const useAppStore = create<ExtendedState>((set, get) => ({
  // Initial state
  generations: [],
  isLoading: true,
  isRefreshing: false,

  settings: {
    model: '',
    ratio: '1:1',
    quality: '',
    creditsPerImage: 0,
    balance: 0,
  },

  prompt: '',
  attachments: [],
  isSending: false,

  selectedGeneration: null,
  menuGeneration: null,
  toasts: [],

  // Internal state
  telegramId: null,
  isInitialized: false,
  models: [],
  selectedModelId: null,
  pollingIntervalId: null,
  trialAvailable: false,

  // Initialize store with telegram user ID
  initialize: async (telegramId: number) => {
    if (get().isInitialized && get().telegramId === telegramId) {
      logger.api.debug('Store already initialized for this user');
      return;
    }

    logger.api.info('Initializing store', { telegramId });
    set({ telegramId, isLoading: true });

    try {
      // Sync user with backend
      await api.syncUser(telegramId);
      logger.api.info('User synced');

      // Load data in parallel
      await Promise.all([get().loadModels(), get().loadBalance(), get().loadGenerations()]);

      // Check trial status
      try {
        const trialStatus = await api.getTrialStatus(telegramId);
        set({ trialAvailable: trialStatus.trial_available });
      } catch {
        logger.api.warn('Failed to get trial status');
      }

      set({ isInitialized: true, isLoading: false });

      // Start polling for active generations
      get().startPolling();

      logger.api.info('Store initialization complete');
    } catch (error) {
      logger.api.error('Store initialization failed', { error });
      set({ isLoading: false });
      get().addToast({ message: 'Failed to load data', type: 'error' });
    }
  },

  // Load available models
  loadModels: async () => {
    try {
      const modelsData = await api.getModels();
      const models: ModelInfo[] = modelsData.map((item) => ({
        id: item.model.id,
        key: item.model.key,
        name: item.model.name,
        options: {
          supports_aspect_ratio: item.model.options.supports_aspect_ratio,
          supports_resolution: item.model.options.supports_resolution,
          supports_quality: item.model.options.supports_quality,
          aspect_ratio_options: item.model.options.aspect_ratio_options,
          resolution_options: item.model.options.resolution_options,
          quality_options: item.model.options.quality_options,
        },
        basePrice: item.prices[0]?.unit_price || 0,
      }));

      // Set default model if not set
      const currentModelId = get().selectedModelId;
      const defaultModel = models[0];

      if (!currentModelId && defaultModel) {
        set({
          models,
          selectedModelId: defaultModel.id,
          settings: {
            ...get().settings,
            model: defaultModel.name,
            ratio: defaultModel.options.aspect_ratio_options?.[0] || '1:1',
            quality: defaultModel.options.resolution_options?.[0] || '',
            creditsPerImage: defaultModel.basePrice,
          },
        });
      } else {
        set({ models });
      }

      logger.api.info('Models loaded', { count: models.length });
    } catch (error) {
      logger.api.error('Failed to load models', { error });
    }
  },

  // Load user balance
  loadBalance: async () => {
    const telegramId = get().telegramId;
    if (!telegramId) return;

    try {
      const balanceData = await api.getBalance(telegramId);
      set({
        settings: {
          ...get().settings,
          balance: balanceData.balance,
        },
      });
      logger.api.debug('Balance loaded', { balance: balanceData.balance });
    } catch (error) {
      logger.api.error('Failed to load balance', { error });
    }
  },

  // Set selected model
  setSelectedModel: (modelId: number) => {
    const model = get().models.find((m) => m.id === modelId);
    if (model) {
      set({
        selectedModelId: modelId,
        settings: {
          ...get().settings,
          model: model.name,
          ratio: model.options.aspect_ratio_options?.[0] || get().settings.ratio,
          quality: model.options.resolution_options?.[0] || get().settings.quality,
          creditsPerImage: model.basePrice,
        },
      });
    }
  },

  // Prompt actions
  setPrompt: (prompt) => set({ prompt }),

  // Attachment actions
  addAttachment: (attachment) => {
    const { attachments } = get();
    if (attachments.length < 3) {
      set({ attachments: [...attachments, attachment] });
    }
  },

  removeAttachment: (id) => {
    const { attachments } = get();
    const attachment = attachments.find((a) => a.id === id);
    if (attachment?.url.startsWith('blob:')) {
      URL.revokeObjectURL(attachment.url);
    }
    set({ attachments: attachments.filter((a) => a.id !== id) });
  },

  clearAttachments: () => {
    const { attachments } = get();
    attachments.forEach((a) => {
      if (a.url.startsWith('blob:')) {
        URL.revokeObjectURL(a.url);
      }
    });
    set({ attachments: [] });
  },

  // Generation submission
  submitGeneration: async () => {
    const { prompt, attachments, settings, telegramId, selectedModelId, models } = get();

    if (!telegramId) {
      logger.generation.error('Cannot submit: not initialized');
      get().addToast({ message: 'Please wait for app to load', type: 'error' });
      return;
    }

    if (!prompt.trim() && attachments.length === 0) {
      logger.generation.warn('Submit cancelled: empty prompt and no attachments');
      return;
    }

    if (!selectedModelId) {
      logger.generation.error('Cannot submit: no model selected');
      get().addToast({ message: 'Please select a model', type: 'error' });
      return;
    }

    const model = models.find((m) => m.id === selectedModelId);
    if (!model) {
      logger.generation.error('Cannot submit: model not found');
      return;
    }

    logger.generation.info('Submitting generation', {
      promptLength: prompt.length,
      attachmentCount: attachments.length,
      mode: attachments.length > 0 ? 'i2i' : 't2i',
      model: model.name,
      ratio: settings.ratio,
      quality: settings.quality,
    });

    set({ isSending: true });

    // Create optimistic generation for immediate UI feedback
    const optimisticId = generateId();
    const optimisticGeneration: GenerationItem = {
      id: optimisticId,
      createdAt: Date.now(),
      mode: attachments.length > 0 ? 'i2i' : 't2i',
      prompt: prompt.trim(),
      attachments: [...attachments],
      model: model.name,
      ratio: settings.ratio,
      quality: settings.quality,
      liked: false,
      status: 'generating',
    };

    // Add optimistic generation to top of feed
    set((state) => ({
      generations: [optimisticGeneration, ...state.generations],
      prompt: '',
      attachments: [],
      isSending: false,
    }));

    try {
      // Upload attachments and get URLs (for now, use the blob URLs - in real app you'd upload to server)
      // TODO: Implement file upload endpoint
      const referenceUrls = attachments
        .filter((a) => !a.url.startsWith('blob:'))
        .map((a) => a.url);

      const response = await api.submitGeneration({
        telegram_id: telegramId,
        model_id: selectedModelId,
        prompt: prompt.trim(),
        aspect_ratio: settings.ratio,
        resolution: settings.quality,
        reference_urls: referenceUrls,
      });

      logger.generation.info('Generation submitted', {
        requestId: response.request.id,
        publicId: response.request.public_id,
        trialUsed: response.trial_used,
      });

      // Update optimistic generation with real ID
      set((state) => ({
        generations: state.generations.map((g) =>
          g.id === optimisticId
            ? {
                ...g,
                id: response.request.public_id,
                status: mapStatus(response.request.status),
              }
            : g
        ),
      }));

      // Refresh balance after submission
      get().loadBalance();

      // Start polling for this generation
      get().startPolling();
    } catch (error) {
      logger.generation.error('Generation submission failed', { error });

      // Update optimistic generation to error state
      set((state) => ({
        generations: state.generations.map((g) =>
          g.id === optimisticId
            ? {
                ...g,
                status: 'error',
                errorMessage:
                  error instanceof ApiError
                    ? error.detail
                    : 'Failed to submit generation',
              }
            : g
        ),
      }));

      const message =
        error instanceof ApiError
          ? error.statusCode === 402
            ? 'Insufficient balance'
            : error.detail
          : 'Failed to submit generation';

      get().addToast({ message, type: 'error' });
    }
  },

  // Retry failed generation
  retryGeneration: async (id) => {
    const { generations, telegramId, selectedModelId } = get();
    const generation = generations.find((g) => g.id === id);

    if (!generation || !telegramId || !selectedModelId) {
      logger.generation.error('Cannot retry: missing data');
      return;
    }

    logger.generation.info('Retrying generation', { generationId: id });

    // Update to generating state
    set((state) => ({
      generations: state.generations.map((g) =>
        g.id === id ? { ...g, status: 'generating', errorMessage: undefined } : g
      ),
    }));

    try {
      const response = await api.submitGeneration({
        telegram_id: telegramId,
        model_id: selectedModelId,
        prompt: generation.prompt,
        aspect_ratio: generation.ratio,
        resolution: generation.quality,
        reference_urls: generation.attachments
          .filter((a) => !a.url.startsWith('blob:'))
          .map((a) => a.url),
      });

      // Update generation with new ID
      set((state) => ({
        generations: state.generations.map((g) =>
          g.id === id
            ? {
                ...g,
                id: response.request.public_id,
                status: mapStatus(response.request.status),
              }
            : g
        ),
      }));

      get().loadBalance();
      get().startPolling();
      logger.generation.info('Retry successful', { newId: response.request.public_id });
    } catch (error) {
      logger.generation.error('Retry failed', { error });
      set((state) => ({
        generations: state.generations.map((g) =>
          g.id === id
            ? {
                ...g,
                status: 'error',
                errorMessage:
                  error instanceof ApiError ? error.detail : 'Retry failed',
              }
            : g
        ),
      }));
      get().addToast({ message: 'Retry failed', type: 'error' });
    }
  },

  // Delete generation (local only for now)
  deleteGeneration: (id) => {
    const { generations } = get();
    logger.generation.info('Deleting generation', { generationId: id });
    const generation = generations.find((g) => g.id === id);
    if (generation) {
      generation.attachments.forEach((a) => {
        if (a.url.startsWith('blob:')) {
          URL.revokeObjectURL(a.url);
        }
      });
    }
    set({ generations: generations.filter((g) => g.id !== id), menuGeneration: null });
    get().addToast({ message: 'Generation deleted', type: 'info' });
  },

  // Toggle like (local only for now)
  toggleLike: (id) => {
    const { generations } = get();
    const generation = generations.find((g) => g.id === id);
    const newLikedState = generation ? !generation.liked : true;
    logger.ui.debug('Toggle like', { generationId: id, liked: newLikedState });
    set({
      generations: generations.map((g) => (g.id === id ? { ...g, liked: !g.liked } : g)),
    });
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
    }
  },

  // UI state
  setSelectedGeneration: (generation) => set({ selectedGeneration: generation }),
  setMenuGeneration: (generation) => set({ menuGeneration: generation }),

  // Toast management
  addToast: (toast) => {
    const id = generateId();
    const newToast: Toast = { ...toast, id, duration: toast.duration ?? 3000 };
    set({ toasts: [...get().toasts, newToast] });
    setTimeout(() => {
      get().removeToast(id);
    }, newToast.duration);
  },

  removeToast: (id) => {
    set({ toasts: get().toasts.filter((t) => t.id !== id) });
  },

  // Load generations from API
  loadGenerations: async () => {
    const telegramId = get().telegramId;
    if (!telegramId) {
      logger.generation.warn('Cannot load generations: not initialized');
      set({ isLoading: false, generations: [] });
      return;
    }

    logger.generation.info('Loading generations...');
    set({ isLoading: true });

    try {
      const response = await api.listGenerations(telegramId);

      const generations: GenerationItem[] = response.items.map((item) => ({
        id: item.public_id,
        createdAt: new Date(item.created_at).getTime(),
        mode: item.mode,
        prompt: item.prompt,
        attachments: item.reference_urls.map((url, idx) => ({
          id: `ref-${idx}`,
          url,
        })),
        resultUrl: item.result_urls[0],
        model: item.model_name,
        ratio: item.aspect_ratio || '1:1',
        quality: item.resolution || item.quality || '',
        liked: false,
        status: mapStatus(item.status),
        errorMessage: item.error_message || undefined,
      }));

      set({ generations, isLoading: false });
      logger.generation.info('Generations loaded', { count: generations.length });
    } catch (error) {
      logger.generation.error('Failed to load generations', { error });
      set({ isLoading: false, generations: [] });
      get().addToast({ message: 'Failed to load generations', type: 'error' });
    }
  },

  // Refresh generations (pull-to-refresh)
  refreshGenerations: async () => {
    logger.generation.info('Refreshing generations...');
    set({ isRefreshing: true });

    await get().loadGenerations();
    await get().loadBalance();

    set({ isRefreshing: false });
    logger.generation.debug('Generations refreshed');
    get().addToast({ message: 'Feed updated', type: 'info' });
  },

  // Update settings
  updateSettings: (newSettings) => {
    logger.ui.debug('Settings updated', { newSettings });
    set({ settings: { ...get().settings, ...newSettings } });
  },

  // Start polling for active generations
  startPolling: () => {
    const existing = get().pollingIntervalId;
    if (existing) {
      return; // Already polling
    }

    logger.api.debug('Starting generation polling');
    const intervalId = setInterval(() => {
      get().pollActiveGeneration();
    }, POLL_INTERVAL);

    set({ pollingIntervalId: intervalId });

    // Also poll immediately
    get().pollActiveGeneration();
  },

  // Stop polling
  stopPolling: () => {
    const intervalId = get().pollingIntervalId;
    if (intervalId) {
      clearInterval(intervalId);
      set({ pollingIntervalId: null });
      logger.api.debug('Stopped generation polling');
    }
  },

  // Poll for active generation updates
  pollActiveGeneration: async () => {
    const { telegramId, generations } = get();
    if (!telegramId) return;

    // Check if there are any generating items
    const generatingItems = generations.filter((g) => g.status === 'generating');
    if (generatingItems.length === 0) {
      get().stopPolling();
      return;
    }

    try {
      // Refresh the full list to get updated statuses
      const response = await api.listGenerations(telegramId, 20);

      // Update only the status and results for existing items
      set((state) => ({
        generations: state.generations.map((gen) => {
          const updated = response.items.find((item) => item.public_id === gen.id);
          if (updated) {
            const newStatus = mapStatus(updated.status);
            // Only update if something changed
            if (newStatus !== gen.status || (updated.result_urls[0] && !gen.resultUrl)) {
              logger.generation.debug('Generation status updated', {
                id: gen.id,
                oldStatus: gen.status,
                newStatus,
                hasResult: !!updated.result_urls[0],
              });
              return {
                ...gen,
                status: newStatus,
                resultUrl: updated.result_urls[0] || gen.resultUrl,
                errorMessage: updated.error_message || gen.errorMessage,
              };
            }
          }
          return gen;
        }),
      }));

      // Refresh balance when generations complete
      const hadGenerating = generatingItems.length > 0;
      const stillGenerating = get().generations.filter((g) => g.status === 'generating').length > 0;
      if (hadGenerating && !stillGenerating) {
        get().loadBalance();
        get().stopPolling();
      }
    } catch (error) {
      logger.api.warn('Polling failed', { error });
    }
  },
}));
