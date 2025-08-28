# Use Debian-based Node (NOT Alpine)
FROM node:24.0.2-slim

# Create app directory
WORKDIR /app

# Install dependencies first (better layer caching)
COPY package*.json ./
RUN npm install

# Copy the rest of the frontend source code
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Start dev server with host binding
CMD ["npm", "run", "dev", "--", "--host"]
