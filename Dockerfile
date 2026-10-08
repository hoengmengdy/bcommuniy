FROM node:22-alpine AS frontend
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html vite.config.js jsconfig.json ./
COPY public ./public
COPY src ./src
RUN npm run build

FROM python:3.13-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_ENV=production HOST=0.0.0.0 PORT=8080
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt \
    && groupadd --system community \
    && useradd --system --gid community --home-dir /app community
COPY --chown=community:community backend ./backend
COPY --from=frontend --chown=community:community /build/dist ./dist
RUN mkdir -p backend/database && chown community:community backend/database
USER community
EXPOSE 8080
CMD ["python", "-m", "backend.production"]
