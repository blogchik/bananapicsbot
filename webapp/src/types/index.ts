/**
 * Core types for BananaPics WebApp
 */

// Generation mode type
export type GenerationMode = 't2i' | 'i2i';

// Generation status
export type GenerationStatus = 'idle' | 'generating' | 'done' | 'error';

// Attachment for image-to-image
export interface Attachment {
  id: string;
  url: string;
  file?: File;
}

// Main generation item
export interface GenerationItem {
  id: string;
  createdAt: number;
  mode: GenerationMode;
  prompt: string;
  attachments: Attachment[];
  resultUrl?: string;
  model: string;
  ratio: string;
  quality: string;
  liked: boolean;
  status: GenerationStatus;
  errorMessage?: string;
}

// User settings/profile
export interface UserSettings {
  model: string;
  ratio: string;
  quality: string;
  creditsPerImage: number;
  balance: number;
}

// Toast notification
export interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
  duration?: number;
  timeoutId?: ReturnType<typeof setTimeout>;
}

// Bottom sheet menu action
export interface MenuAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  onClick: () => void;
  destructive?: boolean;
}

// Telegram WebApp theme params (subset we use)
export interface TelegramThemeParams {
  bg_color?: string;
  text_color?: string;
  hint_color?: string;
  link_color?: string;
  button_color?: string;
  button_text_color?: string;
  secondary_bg_color?: string;
}

// Model info type
export interface ModelInfo {
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

// Store state
export interface AppState {
  // Generations
  generations: GenerationItem[];
  isLoading: boolean;
  isRefreshing: boolean;

  // User settings
  settings: UserSettings;

  // Composer state
  prompt: string;
  attachments: Attachment[];
  isSending: boolean;

  // UI state
  selectedGeneration: GenerationItem | null;
  menuGeneration: GenerationItem | null;
  toasts: Toast[];

  // Actions
  setPrompt: (prompt: string) => void;
  addAttachment: (attachment: Attachment) => void;
  removeAttachment: (id: string) => void;
  clearAttachments: () => void;

  submitGeneration: () => Promise<void>;
  retryGeneration: (id: string) => Promise<void>;
  deleteGeneration: (id: string) => void;
  toggleLike: (id: string) => void;

  setSelectedGeneration: (generation: GenerationItem | null) => void;
  setMenuGeneration: (generation: GenerationItem | null) => void;

  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;

  loadGenerations: () => Promise<void>;
  refreshGenerations: () => Promise<void>;

  updateSettings: (settings: Partial<UserSettings>) => void;
}
