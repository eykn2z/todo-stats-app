FROM node:16-alpine as builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy source and configuration files
COPY . .

# Build the application
RUN npm run build

# Runner stage
FROM node:16-alpine

WORKDIR /app

# Install serve
RUN npm install -g serve

# Copy build files from builder stage
COPY --from=builder /app/build ./build

EXPOSE 3000
CMD ["serve", "-s", "build", "-l", "3000"]