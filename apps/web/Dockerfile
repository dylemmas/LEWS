FROM node:20-alpine

RUN corepack enable && corepack prepare pnpm@9.15.0 --activate

WORKDIR /repo

# Copy workspace root + lockfile first
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml* .npmrc* ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/shared-types/package.json ./packages/shared-types/package.json

RUN pnpm install --filter lews-web... --frozen-lockfile=false

# Copy sources
COPY apps/web ./apps/web
COPY packages ./packages
COPY turbo.json ./

ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /repo/apps/web

EXPOSE 3000

CMD ["pnpm", "dev"]
