# Admin Panel Documentation

## Overview

The BananaPics Admin Panel is a full-featured web dashboard for managing the bot, users, payments, generations, and broadcasts. Built with React 18, TypeScript, and Vite, it provides a modern, responsive interface for administrators.

## Access

### URL
- **Local Development**: http://localhost:3034
- **Production**: https://your-domain.com (configure in deployment)

### Authentication

The admin panel uses **Telegram Login Widget** authentication:

1. Navigate to the admin panel URL
2. Click "Sign in with Telegram"
3. Authorize the bot in Telegram
4. You'll be redirected to the dashboard

**Requirements:**
- Your Telegram user ID must be in the `ADMIN_IDS` environment variable
- The bot username must be configured (`VITE_BOT_USERNAME`)

**Security:**
- HMAC-SHA256 verification of Telegram auth data
- JWT tokens with secure HttpOnly storage
- Admin-only access enforcement
- Automatic session validation

## Features

### 1. Dashboard

**Statistics Overview:**
- Total users, active users (7d/30d)
- New users (today, week, month)
- Total generations and success rate
- Revenue metrics (deposits, spent, net)
- Banned users count

**Charts:**
- Daily user registrations (line chart)
- Daily generation volume (area chart)
- Daily revenue trends (bar chart)
- Generation breakdown by model (pie chart)

**Date Range Selection:**
- Last 7 days
- Last 30 days
- Last 90 days
- Custom date range

### 2. User Management

**User List:**
- Search by Telegram ID, username, or name
- Pagination (50 users per page)
- Sortable columns
- Quick actions (view, ban, adjust credits)

**User Detail View:**
- Profile information
- Current balance
- Referral stats
- Recent generations
- Payment history
- Admin actions (ban/unban, adjust credits)

**Credit Adjustment:**
- Add or remove credits
- Reason tracking
- Balance history

### 3. Broadcast Management

**Create Broadcast:**
- Content types: text, photo, video, audio, sticker
- Rich text formatting
- Media upload
- Custom inline button (text + URL)

**Recipient Filtering:**
- All users
- Active users (7d)
- Active users (30d)
- Users with balance
- Paid users only
- New users (last 7d)

**Broadcast Control:**
- Preview before sending
- Start broadcast
- Pause/cancel active broadcast
- Real-time progress tracking

**Broadcast Stats:**
- Total users targeted
- Messages sent
- Failed deliveries
- Blocked by users
- Progress percentage

### 4. Payment Management

**Payment List:**
- All payment transactions
- Filter by status
- Sort by date/amount
- Pagination

**Payment Details:**
- Transaction ID
- User information
- Amount (Stars and credits)
- Status
- Timestamp

**Refund System:**
- Refund Telegram Stars payments
- Automatic credit deduction
- Refund status tracking
- Error handling for Telegram API

### 5. Generation Management

**Generation List:**
- All generations (paginated)
- Filter by status (completed, failed, processing)
- Sort by date
- User information
- Model used

**Generation Details:**
- Prompt text
- Model and parameters
- Status and timestamps
- Credit cost
- Result images (if completed)

**Actions:**
- View generation
- Refund failed generation
- Queue monitoring

### 6. Model Management

**Model List:**
- All available models
- Current pricing
- Generation count
- Active/inactive status

**Model Configuration:**
- Toggle model availability
- Update display name
- Adjust base price
- View usage statistics

### 7. System Settings

**Configurable Settings:**
- Generation price markup
- Referral bonus percentage
- Referral join bonus
- Stars exchange rates
- Payment presets
- Rate limits

**Settings Management:**
- Real-time updates
- No restart required
- Change tracking
- Admin audit log

## Technical Architecture

### Frontend Stack

```
React 18           - UI framework
TypeScript         - Type safety
Vite               - Build tool & dev server
TanStack Router    - Type-safe routing
Zustand            - State management
TanStack Query     - Data fetching & caching
Recharts           - Data visualization
TailwindCSS        - Utility-first CSS
Lucide React       - Icon library
shadcn/ui          - Component library
```

### Project Structure

```
admin-panel/
├── src/
│   ├── api/              # API client layer
│   │   ├── client.ts     # Axios instance
│   │   ├── auth.ts       # Authentication
│   │   ├── admin.ts      # Admin endpoints
│   │   ├── users.ts      # User management
│   │   ├── broadcasts.ts # Broadcast system
│   │   └── ...
│   ├── components/       # React components
│   │   ├── layout/       # Layout components
│   │   ├── charts/       # Chart components
│   │   └── ui/           # UI primitives
│   ├── pages/            # Page components
│   │   ├── DashboardPage.tsx
│   │   ├── users/        # User pages
│   │   ├── broadcasts/   # Broadcast pages
│   │   └── ...
│   ├── stores/           # Zustand stores
│   │   └── authStore.ts  # Auth state
│   ├── lib/              # Utilities
│   │   └── utils.ts
│   ├── App.tsx           # App root
│   └── main.tsx          # Entry point
├── public/               # Static assets
├── Dockerfile            # Production build
├── nginx.conf            # Nginx config
├── vite.config.ts        # Vite config
└── package.json          # Dependencies
```

### API Integration

**Base URL:** `/api/v1/admin` (proxied via nginx)

**Authentication:**
- JWT Bearer tokens in Authorization header
- Automatic token refresh
- 401 handling with redirect to login

**Endpoints:**
- `POST /auth/login` - Telegram login
- `GET /auth/me` - Get current admin
- `GET /stats` - Dashboard statistics
- `GET /users` - List users
- `GET /users/{id}` - Get user details
- `POST /users/{id}/ban` - Ban user
- `POST /credits` - Adjust credits
- `POST /broadcasts` - Create broadcast
- `GET /broadcasts` - List broadcasts
- `POST /broadcasts/{id}/start` - Start broadcast
- `GET /payments` - List payments
- `GET /generations` - List generations
- `GET /models` - List models
- `PATCH /models/{id}` - Update model
- `GET /settings` - Get settings
- `PATCH /settings` - Update settings

### State Management

**AuthStore (Zustand):**
```typescript
interface AuthState {
  token: string | null
  admin: AdminUser | null
  isAuthenticated: boolean
  setAuth: (token: string, admin: AdminUser) => void
  logout: () => void
}
```

**TanStack Query:**
- Automatic caching
- Background refetching
- Optimistic updates
- Error handling
- Loading states

### Build & Deployment

**Docker Build:**

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_BOT_USERNAME
ARG VITE_API_URL
ENV VITE_BOT_USERNAME=$VITE_BOT_USERNAME
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Production stage
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 3034
CMD ["nginx", "-g", "daemon off;"]
```

**Nginx Configuration:**

```nginx
server {
    listen 3034;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://api:9000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## Environment Variables

### Build-time Variables

These must be provided during Docker build:

```env
VITE_BOT_USERNAME=BananaPicsBot    # Bot username (without @)
VITE_API_URL=/api/v1               # API base URL
```

### Backend Variables

Required in API service `.env`:

```env
ADMIN_JWT_SECRET=your-secret-key   # JWT signing secret
ADMIN_IDS=123456789,987654321      # Comma-separated admin IDs
```

## Deployment

### Docker Compose

The admin panel is included in `docker-compose.yml`:

```yaml
admin-panel:
  build:
    context: ./admin-panel
    args:
      VITE_BOT_USERNAME: ${VITE_BOT_USERNAME}
      VITE_API_URL: ${VITE_API_URL:-/api/v1}
  image: ghcr.io/blogchik/bananapicsbot/admin-panel:latest
  ports:
    - "3034:3034"
  networks:
    - app_net
  depends_on:
    api:
      condition: service_healthy
```

### CI/CD (GitHub Actions)

The workflow automatically builds and deploys:

```yaml
- name: Build and push admin-panel
  uses: docker/build-push-action@v5
  with:
    context: ./admin-panel
    push: true
    build-args: |
      VITE_BOT_USERNAME=BananaPicsBot
      VITE_API_URL=/api/v1
```

### Production Setup

1. **Domain & SSL:**
   ```nginx
   server {
       listen 443 ssl http2;
       server_name admin.yourdomain.com;

       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;

       location / {
           proxy_pass http://localhost:3034;
           # ... proxy headers
       }
   }
   ```

2. **Environment:**
   - Set `ADMIN_PANEL_URL` in `.env`
   - Configure `ADMIN_JWT_SECRET`
   - Add admin IDs to `ADMIN_IDS`

3. **Security:**
   - Use HTTPS in production
   - Set strong JWT secret (32+ characters)
   - Enable rate limiting
   - Configure CORS properly

## Development

### Local Setup

```bash
cd admin-panel
npm install
npm run dev
```

The dev server runs on http://localhost:5173 with hot reload.

### Build

```bash
npm run build
```

Output in `dist/` directory.

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

## Troubleshooting

### "Bot username not configured" Error

**Cause:** `VITE_BOT_USERNAME` not available at build time

**Solution:**
1. Check `.env` has `VITE_BOT_USERNAME=YourBotName`
2. Rebuild: `docker compose build --no-cache admin-panel`
3. For CI/CD, ensure build args are passed in workflow

### Login Redirect Loop

**Cause:** JWT auth flow mismatch

**Solution:**
1. Clear browser localStorage
2. Check API endpoint returns `access_token` field
3. Verify `ADMIN_JWT_SECRET` is set
4. Check your user ID is in `ADMIN_IDS`

### API 401 Errors

**Cause:** Invalid or expired JWT token

**Solution:**
1. Logout and login again
2. Check token expiration time
3. Verify JWT secret matches between services

### Charts Not Loading

**Cause:** API endpoint errors or data format issues

**Solution:**
1. Check browser console for errors
2. Verify API endpoints respond correctly
3. Check date range parameters

## Best Practices

### Security
- Always use HTTPS in production
- Rotate JWT secrets regularly
- Monitor admin actions
- Implement IP whitelisting for extra security
- Use strong passwords for database

### Performance
- Enable nginx caching for static assets
- Use CDN for production
- Optimize images
- Monitor API response times
- Implement query caching

### Maintenance
- Regular backups
- Monitor error logs
- Update dependencies
- Test before deploying
- Keep documentation updated

## Future Enhancements

- [ ] Two-factor authentication
- [ ] Admin action audit log
- [ ] Export data to CSV/Excel
- [ ] Advanced analytics
- [ ] Real-time notifications
- [ ] Bulk user operations
- [ ] Custom dashboard widgets
- [ ] Role-based access control
- [ ] API rate limit monitoring
- [ ] System health monitoring
