import { create } from 'zustand';
import type { AppState, GenerationItem, Toast } from '../types';

// Generate unique ID using crypto API
const generateId = () => crypto.randomUUID();

// Mock delay to simulate API calls
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Mock image URLs for demo
const MOCK_IMAGES = [
  'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=800&q=80', // banana
  'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800&q=80', // portrait
  'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=800&q=80', // model
  'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=800&q=80', // woman
  'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=800&q=80', // man portrait
];

// Initial mock generations data
const INITIAL_GENERATIONS: GenerationItem[] = [
  {
    id: '1',
    createdAt: Date.now() - 3600000,
    mode: 't2i',
    prompt: 'Full-body portrait of the reference woman standing upright, neutral pose with relaxed arms, simple modern outfit (solid-color shirt and jeans), clean white studio background, softbox lighting from both sides, photorealistic ultra-detailed texture, realistic skin tone, fine hair detail, cinematic color grading, 4K resolution, sharp focus, professional fashion photo style.',
    attachments: [],
    resultUrl: MOCK_IMAGES[1],
    model: 'Nano Banana Pro',
    ratio: '9:16',
    quality: 'High (4K)',
    liked: true,
    status: 'done',
  },
  {
    id: '2',
    createdAt: Date.now() - 7200000,
    mode: 'i2i',
    prompt: 'A ripe yellow banana on a neutral gray background, studio lighting, product photography style, high detail',
    attachments: [{ id: 'a1', url: MOCK_IMAGES[0] }],
    resultUrl: MOCK_IMAGES[0],
    model: 'Nano Banana Pro',
    ratio: '16:9',
    quality: 'High (4K)',
    liked: false,
    status: 'done',
  },
];

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  generations: [],
  isLoading: true,
  isRefreshing: false,

  settings: {
    model: 'Nano Banana Pro',
    ratio: '16:9',
    quality: 'High (4K)',
    creditsPerImage: 240,
    balance: 1200,
  },

  prompt: '',
  attachments: [],
  isSending: false,

  selectedGeneration: null,
  menuGeneration: null,
  toasts: [],

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
    // Revoke Object URL to prevent memory leak
    const attachment = attachments.find((a) => a.id === id);
    if (attachment?.url.startsWith('blob:')) {
      URL.revokeObjectURL(attachment.url);
    }
    set({ attachments: attachments.filter((a) => a.id !== id) });
  },

  clearAttachments: () => {
    const { attachments } = get();
    // Revoke all Object URLs to prevent memory leaks
    attachments.forEach((a) => {
      if (a.url.startsWith('blob:')) {
        URL.revokeObjectURL(a.url);
      }
    });
    set({ attachments: [] });
  },

  // Generation submission
  submitGeneration: async () => {
    const { prompt, attachments, settings, generations } = get();

    if (!prompt.trim() && attachments.length === 0) return;

    set({ isSending: true });

    // Create optimistic generation
    const newGeneration: GenerationItem = {
      id: generateId(),
      createdAt: Date.now(),
      mode: attachments.length > 0 ? 'i2i' : 't2i',
      prompt: prompt.trim(),
      attachments: [...attachments],
      model: settings.model,
      ratio: settings.ratio,
      quality: settings.quality,
      liked: false,
      status: 'generating',
    };

    // Add to top of feed
    set({
      generations: [newGeneration, ...generations],
      prompt: '',
      attachments: [],
      isSending: false,
    });

    // Simulate generation delay (2-4 seconds)
    await delay(2000 + Math.random() * 2000);

    // Simulate success/failure (90% success rate)
    const success = Math.random() > 0.1;

    set({
      generations: get().generations.map((g) =>
        g.id === newGeneration.id
          ? {
              ...g,
              status: success ? 'done' : 'error',
              resultUrl: success ? MOCK_IMAGES[Math.floor(Math.random() * MOCK_IMAGES.length)] : undefined,
              errorMessage: success ? undefined : 'Generation failed. Please try again.',
            }
          : g
      ),
    });

    if (!success) {
      get().addToast({ message: 'Generation failed', type: 'error' });
    }
  },

  // Retry failed generation
  retryGeneration: async (id) => {
    const { generations } = get();

    set({
      generations: generations.map((g) =>
        g.id === id ? { ...g, status: 'generating', errorMessage: undefined } : g
      ),
    });

    await delay(2000 + Math.random() * 2000);

    // Higher success rate on retry
    const success = Math.random() > 0.05;

    set({
      generations: get().generations.map((g) =>
        g.id === id
          ? {
              ...g,
              status: success ? 'done' : 'error',
              resultUrl: success ? MOCK_IMAGES[Math.floor(Math.random() * MOCK_IMAGES.length)] : undefined,
              errorMessage: success ? undefined : 'Generation failed again. Please try later.',
            }
          : g
      ),
    });

    if (success) {
      get().addToast({ message: 'Generation complete!', type: 'success' });
    } else {
      get().addToast({ message: 'Retry failed', type: 'error' });
    }
  },

  // Delete generation
  deleteGeneration: (id) => {
    const { generations } = get();
    // Revoke Object URLs from attachments to prevent memory leaks
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

  // Toggle like
  toggleLike: (id) => {
    const { generations } = get();
    set({
      generations: generations.map((g) => (g.id === id ? { ...g, liked: !g.liked } : g)),
    });
    // Telegram haptic feedback
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

    // Auto-remove after duration
    setTimeout(() => {
      get().removeToast(id);
    }, newToast.duration);
  },

  removeToast: (id) => {
    set({ toasts: get().toasts.filter((t) => t.id !== id) });
  },

  // Load generations (initial load)
  loadGenerations: async () => {
    set({ isLoading: true });
    await delay(1500); // Simulate API call
    set({ generations: INITIAL_GENERATIONS, isLoading: false });
  },

  // Refresh generations (pull-to-refresh)
  refreshGenerations: async () => {
    set({ isRefreshing: true });
    await delay(1000);
    set({ isRefreshing: false });
    get().addToast({ message: 'Feed updated', type: 'info' });
  },

  // Update settings
  updateSettings: (newSettings) => {
    set({ settings: { ...get().settings, ...newSettings } });
  },
}));

// Telegram WebApp type declarations
declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        ready: () => void;
        expand: () => void;
        close: () => void;
        MainButton: {
          text: string;
          color: string;
          textColor: string;
          isVisible: boolean;
          isActive: boolean;
          show: () => void;
          hide: () => void;
          onClick: (callback: () => void) => void;
        };
        BackButton: {
          isVisible: boolean;
          show: () => void;
          hide: () => void;
          onClick: (callback: () => void) => void;
        };
        HapticFeedback: {
          impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void;
          notificationOccurred: (type: 'error' | 'success' | 'warning') => void;
          selectionChanged: () => void;
        };
        themeParams: {
          bg_color?: string;
          text_color?: string;
          hint_color?: string;
          link_color?: string;
          button_color?: string;
          button_text_color?: string;
          secondary_bg_color?: string;
        };
        colorScheme: 'light' | 'dark';
        viewportHeight: number;
        viewportStableHeight: number;
        headerColor: string;
        backgroundColor: string;
        isExpanded: boolean;
        initDataUnsafe: {
          user?: {
            id: number;
            first_name: string;
            last_name?: string;
            username?: string;
            language_code?: string;
          };
        };
        setHeaderColor: (color: string) => void;
        setBackgroundColor: (color: string) => void;
      };
    };
  }
}
