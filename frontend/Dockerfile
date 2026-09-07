FROM node:18-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# Build step is skipped in development or done at container start
# For a standard development setup:
CMD ["npm", "run", "dev"]
