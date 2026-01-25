# Telegram Mini App (Webapp)

## Umumiy ko'rinish

BananaPics Telegram Mini App - React + TypeScript asosidagi SPA, Telegram WebApp SDK bilan integratsiya qilingan. AI rasm generatsiya qilish uchun mobil-first interfeys taqdim etadi.

## Texnologiyalar

- **React 18** - UI framework
- **TypeScript** - type safety
- **Vite** - build tool
- **Zustand** - state management
- **Framer Motion** - animatsiyalar
- **TailwindCSS** - styling

## Loyiha strukturasi

```
webapp/
├── src/
│   ├── components/          # UI komponentlari
│   │   ├── AttachmentChips.tsx    # Reference rasm chipslari
│   │   ├── BottomSheetMenu.tsx    # Bottom sheet menyu
│   │   ├── ComposerBar.tsx        # Prompt input va send
│   │   ├── EmptyState.tsx         # Bo'sh holat ko'rinishi
│   │   ├── FullscreenViewer.tsx   # Rasm to'liq ekran
│   │   ├── GenerationCard.tsx     # Generation kartasi
│   │   ├── GenerationFeed.tsx     # Generationlar feed
│   │   ├── HeaderBar.tsx          # Yuqori header
│   │   ├── Icons.tsx              # SVG ikonlar
│   │   ├── TelegramGate.tsx       # Auth blocker ekran
│   │   ├── Toast.tsx              # Notification toastlar
│   │   └── index.ts               # Export barrel
│   ├── hooks/
│   │   └── useTelegram.ts         # Telegram WebApp SDK hook
│   ├── pages/
│   │   └── GenerationsPage.tsx    # Asosiy sahifa
│   ├── services/
│   │   └── api.ts                 # API client
│   ├── store/
│   │   └── index.ts               # Zustand store
│   ├── types/
│   │   └── index.ts               # TypeScript types
│   ├── App.tsx                    # Root komponent
│   ├── main.tsx                   # Entry point
│   └── vite-env.d.ts              # Vite types
├── dist/                    # Build output
├── index.html               # HTML template
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

## Xavfsizlik: Telegram initData Validatsiyasi

### Arxitektura

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Webapp)                         │
├─────────────────────────────────────────────────────────────┤
│  1. Telegram muhitini tekshirish                            │
│     - window.Telegram.WebApp.initData mavjudligi            │
│     - Bo'lmasa → TelegramGate (bloklangan ekran)            │
│                                                             │
│  2. API so'rovlarga initData header qo'shish                │
│     - X-Telegram-Init-Data: <raw initData string>           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (API)                             │
├─────────────────────────────────────────────────────────────┤
│  1. HMAC-SHA256 imzo validatsiyasi                          │
│     - secret = HMAC(bot_token, "WebAppData")                │
│     - hash = HMAC(data_check_string, secret)                │
│                                                             │
│  2. Freshness tekshirish                                    │
│     - auth_date + 24 soat > current_time                    │
│                                                             │
│  3. User ID mosligini tekshirish                            │
│     - request.telegram_id == initData.user.id               │
└─────────────────────────────────────────────────────────────┘
```

### TelegramGate komponenti

Agar webapp Telegram'dan ochilmagan bo'lsa, `TelegramGate` komponenti ko'rsatiladi:

- Shield + lock ikonka
- "Use @BananPicsBot to launch app." xabari
- Bot linkiga o'tish imkoniyati

```tsx
// App.tsx
function App() {
  const { isReady, isAuthorized } = useTelegram();

  if (!isReady) return <Loading />;
  if (!isAuthorized) return <TelegramGate />;

  return <GenerationsPage />;
}
```

### useTelegram Hook

```typescript
// hooks/useTelegram.ts
export function useTelegram() {
  // States
  const [isReady, setIsReady] = useState(false);
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [user, setUser] = useState<TelegramUser | null>(null);

  useEffect(() => {
    const tg = window.Telegram?.WebApp;

    // Telegram muhitini tekshirish
    if (tg && tg.initData && tg.initData.length > 0) {
      globalInitData = tg.initData;  // API uchun saqlash
      tg.ready();
      tg.expand();
      setIsAuthorized(true);
      // ... user extraction
    } else {
      setIsAuthorized(false);  // Blokirovka
    }

    setIsReady(true);
  }, []);

  return {
    isReady,
    isAuthorized,
    user,
    initData: globalInitData,
    hapticImpact,
    hapticNotification,
    // ...
  };
}
```

### API Client

Barcha API so'rovlari avtomatik `X-Telegram-Init-Data` header qo'shadi:

```typescript
// services/api.ts
async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const initData = getInitData();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (initData) {
    headers['X-Telegram-Init-Data'] = initData;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // ... error handling
}
```

## Komponentlar

### ComposerBar

Pastki qismdagi input bar:

- **Prompt textarea** - auto-resize, Enter yuborish
- **Plus (+) tugmasi** - reference rasm qo'shish
  - Maximum 3 ta rasm
  - 3 ta bo'lganda tugma yo'qoladi (animation bilan)
- **Send tugmasi** - generatsiya yuborish
- **Credits indikator** - narx ko'rsatish

```tsx
// Attachment limit
{attachments.length < 3 && (
  <motion.div
    initial={{ scale: 0, opacity: 0 }}
    animate={{ scale: 1, opacity: 1 }}
    exit={{ scale: 0, opacity: 0 }}
    transition={{ type: 'spring', stiffness: 400, damping: 25 }}
  >
    <button onClick={() => fileInputRef.current?.click()}>
      <PlusIcon />
    </button>
  </motion.div>
)}
```

**Fayl validatsiya:**
- Ruxsat etilgan formatlar: JPG, PNG, WebP, GIF, BMP, TIFF
- Maksimal hajm: 20MB
- Limit: 3 ta rasm

### GenerationFeed

Generatsiyalar ro'yxati:

- Pull-to-refresh
- Skeleton loading
- Empty state

### GenerationCard

Har bir generatsiya kartasi:

- Status indikatori (generating, done, error)
- Rasm preview
- Like tugmasi
- Context menu (delete, retry)

### FullscreenViewer

Rasmni to'liq ekranda ko'rish:

- Pinch-to-zoom
- Swipe to close
- Share/download

### Toast

Notification tizimi:

```typescript
// Types: success, error, info, warning
addToast({ message: "Generation complete!", type: 'success' });
```

## State Management (Zustand)

```typescript
// store/index.ts
interface AppState {
  // Generations
  generations: GenerationItem[];
  isLoading: boolean;
  isRefreshing: boolean;

  // Composer
  prompt: string;
  attachments: Attachment[];
  isSending: boolean;

  // Settings
  settings: {
    model: string;
    ratio: string;
    quality: string;
    creditsPerImage: number;
    balance: number;
  };

  // UI
  selectedGeneration: GenerationItem | null;
  menuGeneration: GenerationItem | null;
  toasts: Toast[];

  // Actions
  setPrompt: (prompt: string) => void;
  addAttachment: (attachment: Attachment) => void;
  removeAttachment: (id: string) => void;
  submitGeneration: () => Promise<void>;
  toggleLike: (id: string) => void;
  // ...
}
```

## Telegram WebApp SDK Integratsiya

### Initialization

```typescript
const tg = window.Telegram.WebApp;
tg.ready();           // App tayyor signali
tg.expand();          // To'liq ekranga kengaytirish
tg.setHeaderColor('#121212');
tg.setBackgroundColor('#121212');
```

### Haptic Feedback

```typescript
const { hapticImpact, hapticNotification, hapticSelection } = useTelegram();

// Button press
hapticImpact('light');

// Success/error notification
hapticNotification('success');
hapticNotification('error');

// Selection change
hapticSelection();
```

### Theme Support

```typescript
const colorScheme = tg.colorScheme;  // 'light' | 'dark'
const themeParams = tg.themeParams;  // Tema ranglari
```

## Styling

### TailwindCSS konfigurasiya

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        dark: {
          400: '#1a1a24',
          500: '#121212',
          600: '#0a0a0f',
        },
        banana: {
          400: '#ffd666',
          500: '#ffcc00',
          600: '#e6b800',
        },
        surface: '#1e1e2a',
        'surface-light': '#2a2a3a',
      },
    },
  },
};
```

### Custom Utilities

```css
/* Safe area insets */
.pb-safe { padding-bottom: env(safe-area-inset-bottom); }

/* Glow effect */
.shadow-glow { box-shadow: 0 0 20px rgba(255, 204, 0, 0.3); }
```

## Build & Deploy

### Development

```bash
cd webapp
npm install
npm run dev        # http://localhost:5173
```

### Production Build

```bash
npm run build      # dist/ papkasiga output
```

### Docker

```dockerfile
# webapp/Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3033
```

### Environment Variables

```env
VITE_API_URL=/api/v1          # API base URL
```

## API Endpoints

Webapp quyidagi API endpointlardan foydalanadi:

| Endpoint | Method | Tavsif |
|----------|--------|--------|
| `/users/sync` | POST | User yaratish/sync |
| `/users/{id}/balance` | GET | Balans olish |
| `/users/{id}/trial` | GET | Trial holati |
| `/generations/price` | POST | Narx hisoblash |
| `/generations/submit` | POST | Generation boshlash |
| `/generations/active` | GET | Aktiv generation |
| `/generations/{id}` | GET | Generation holati |
| `/generations/{id}/refresh` | POST | Status yangilash |
| `/generations/{id}/results` | GET | Natija rasmlar |
| `/models` | GET | Modellar ro'yxati |

Barcha endpointlar `X-Telegram-Init-Data` header talab qiladi (401 Unauthorized).

## Error Handling

```typescript
// ApiError class
class ApiError extends Error {
  constructor(
    public statusCode: number,
    public detail: string,
    public data?: unknown
  ) {
    super(detail);
  }
}

// Usage
try {
  await api.submitGeneration(data);
} catch (error) {
  if (error instanceof ApiError) {
    if (error.statusCode === 401) {
      // Unauthorized - redirect to bot
    } else if (error.statusCode === 403) {
      // Forbidden - wrong user
    }
    addToast({ message: error.detail, type: 'error' });
  }
}
```

## Performance

### Lazy Loading

```typescript
// React.lazy for code splitting
const FullscreenViewer = lazy(() => import('./components/FullscreenViewer'));
```

### Image Optimization

- Thumbnail preview (compressed)
- Full resolution on tap
- Object URL cleanup (memory leak prevention)

```typescript
// Cleanup on unmount
useEffect(() => {
  return () => {
    attachments.forEach(a => {
      if (a.url.startsWith('blob:')) {
        URL.revokeObjectURL(a.url);
      }
    });
  };
}, [attachments]);
```

### Memoization

```typescript
// memo for expensive components
export const ComposerBar = memo(function ComposerBar() {
  // ...
});

// useCallback for handlers
const handleSend = useCallback(async () => {
  // ...
}, [dependencies]);
```

## Testing

### Manual Testing

1. **Browser test** - localhost:5173 ochish → TelegramGate ko'rinadi
2. **Telegram test** - BotFather WebApp orqali ochish → App ishlaydi
3. **API test** - Network tab da X-Telegram-Init-Data header tekshirish

### Unit Tests (planned)

```bash
npm run test
```

## Troubleshooting

### Muammolar va yechimlar

| Muammo | Sabab | Yechim |
|--------|-------|--------|
| TelegramGate ko'rinadi | initData yo'q | Telegram orqali ochish |
| 401 Unauthorized | initData expired | Appni qayta ochish |
| 403 Forbidden | Noto'g'ri user ID | Request payload tekshirish |
| Blank screen | JS error | Console.log tekshirish |

### Debug Mode

```typescript
// Development da console logging
if (import.meta.env.DEV) {
  console.log('initData:', getInitData());
  console.log('user:', user);
}
```
