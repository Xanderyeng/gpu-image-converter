# ============================================
# GPU Image Converter - Frontend Dockerfile
# ============================================

# Base stage - dependencies
FROM oven/bun:1 AS base
WORKDIR /app

# Copy package files
COPY package.json bun.lockb* ./

# ============================================
# Development stage
# ============================================
FROM base AS development
RUN bun install

COPY . .

EXPOSE 3000

CMD ["bun", "run", "dev"]

# ============================================
# Production dependencies stage
# ============================================
FROM base AS deps
RUN bun install --production

# ============================================
# Builder stage
# ============================================
FROM base AS builder
RUN bun install

COPY . .

# Build the Next.js application
ENV NEXT_TELEMETRY_DISABLED=1
RUN bun run build

# ============================================
# Production stage
# ============================================
FROM oven/bun:1-slim AS production
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["bun", "server.js"]
