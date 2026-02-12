# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy source files
COPY . .

# Accept build arguments for Vite environment variables
ARG VITE_BOT_USERNAME
ARG VITE_API_URL

# Set environment variables for build
ENV VITE_BOT_USERNAME=$VITE_BOT_USERNAME
ENV VITE_API_URL=$VITE_API_URL

# Build the application
RUN npm run build

# Production stage - serve with nginx
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 3034

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
