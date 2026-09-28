# Small official base image (alpine ~50MB vs ~400MB+ for the full image)
FROM node:24-alpine

# Working directory inside the container
WORKDIR /app

# Copy package files first so the dependency layer is cached
COPY package*.json ./

# Install exact versions from the lock file, production dependencies only
RUN npm ci --omit=dev

# Copy the rest of the application code
COPY . .

ENV NODE_ENV=production

# Run as the non-root "node" user
USER node

EXPOSE 3000

# Let Docker check the app's health every 15 seconds
HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
  CMD wget -qO- http://localhost:3000/health || exit 1

# Run node directly (not npm start) so SIGTERM reaches the app
CMD ["node", "server.js"]