# Admin Panel Documentation

## Overview

The BananaPics Admin Panel is a full-featured web dashboard for managing the bot, users, payments, generations, and broadcasts. Built with React 18, TypeScript, and Vite, it provides a modern, responsive interface for administrators.

**Key Features:**
- Real-time Telegram user profile fetching (username, name, photo)
- Generation image previews with thumbnails and full-size modal
- Broadcast progress tracking with status-based coloring
- Comprehensive system settings management
- User management with credit adjustments and ban controls

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
- **Access Denied** - Beautiful error page shown if user is not an admin

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
- **User avatars** fetched from Telegram API with fallback initials
- **Full names** (first_name, last_name) from Telegram
- **Usernames** displayed below names
- Search by Telegram ID, username, or name
- Pagination (50 users per page)
- Quick actions (view, ban, adjust credits)

**User Detail View:**
- **Profile photo** from Telegram (real-time fetch)
- **Full user info**: name, username, language, Telegram ID
- **Statistics**: Balance, Trial Remaining, Generations, Referrals
- **Financial**: Total Deposits (stars), Total Spent (credits)
- **Referral info**: Code, Referrer link
- **Recent generations** with:
  - Model name and key
  - Prompt preview
  - Credit cost
  - Status badge
  - **Thumbnail images** (click to open full size)
- **Payment history**
- Admin actions (ban/unban, adjust credits)

**Credit Adjustment:**
- Add or remove credits
- Reason tracking
- Balance history

**Ban System:**
- Ban users with optional reason
- Banned users cannot use the bot
- Ban notification sent to user in their language (uz/ru/en)
- Ban reason displayed in admin panel
- Unban restores full access
- Unban notification sent to user

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

**Progress Bar Features:**
- **Status-based coloring**:
  - Running: Yellow (banana-500)
  - Completed: Green (100%)
  - Failed: Red
  - Cancelled: Gray
- Percentage display
- Sent/Total count with failed indicator

### 4. Payment Management

**Payment List:**
- All payment transactions
- **User ID links** to user detail page
- Filter by status
- Sort by date/amount
- Pagination

**Payment Details:**
- Transaction ID
- User information (clickable link)
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
- **User ID links** to user detail page
- Filter by status (completed, failed, processing)
- Sort by date
- Model used

**Generation Row Features:**
- User Telegram ID (clickable)
- Model name and key
- Expandable prompt
- Status badge with animation
- Credit cost
- **Thumbnail previews** (up to 3 images shown)
- Click thumbnails to open full-size modal

**Image Preview Modal:**
- Full-size images
- Multiple images in grid
- Click outside to close

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

**Comprehensive Settings Categories:**

**Trial Settings:**
- Trial generations limit (0-100)

**Pricing & Credits:**
- Generation price markup
- Stars exchange numerator/denominator
- Minimum stars purchase

**Referral Program:**
- Referral bonus percent (0-100%)
- Referral join bonus credits

**Generation Limits:**
- Max parallel generations per user
- Poll interval (seconds)
- Max poll duration (seconds)

**Rate Limits:**
- Requests per second
- Burst limit

**Wavespeed API:**
- API timeout
- Minimum balance alert
- Balance cache TTL

**Cache & Performance:**
- Default cache TTL
- Active generation TTL

**Settings Management:**
- Real-time updates
- No restart required
- Change tracking with toast notifications
- Input validation with min/max limits

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
- `POST /admin/auth/login` - Telegram login
- `GET /admin/auth/me` - Get current admin
- `GET /admin/stats` - Dashboard statistics
- `GET /admin/charts/users-daily` - Daily user registrations
- `GET /admin/charts/generations-daily` - Daily generations
- `GET /admin/charts/revenue-daily` - Daily revenue
- `GET /admin/charts/models-breakdown` - Generations by model
- `GET /admin/users` - List users
- `GET /admin/users/{telegram_id}` - Get user details
- `POST /admin/users/{telegram_id}/ban` - Ban user
- `POST /admin/users/{telegram_id}/unban` - Unban user
- `POST /admin/credits` - Adjust user credits
- `GET /admin/users/{telegram_id}/generations` - User generations
- `GET /admin/users/{telegram_id}/payments` - User payments
- `GET /admin/broadcasts/users-count` - Get recipient count
- `POST /admin/broadcasts` - Create broadcast
- `GET /admin/broadcasts` - List broadcasts
- `GET /admin/broadcasts/{public_id}` - Get broadcast status
- `POST /admin/broadcasts/{public_id}/start` - Start broadcast
- `POST /admin/broadcasts/{public_id}/cancel` - Cancel broadcast
- `GET /admin/payments` - List payments
- `GET /admin/payments/daily` - Daily payment stats
- `GET /admin/generations` - List generations
- `GET /admin/generations/queue` - Queue status
- `GET /admin/models` - List models
- `PATCH /admin/models/{model_id}` - Update model
- `PUT /admin/models/{model_id}/price` - Update model price
- `GET /admin/settings` - Get settings
- `PATCH /admin/settings` - Update settings

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
