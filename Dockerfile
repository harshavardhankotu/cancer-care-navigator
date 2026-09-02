# ---- Stage 1: build the React frontend ----
FROM node:20-alpine AS frontend
WORKDIR /fe
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund
COPY frontend .
RUN npm run build

# ---- Stage 2: single Python process serves API + built app ----
FROM python:3.11-slim
WORKDIR /app/backend
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend .
COPY --from=frontend /fe/dist ../frontend/dist
ENV STORAGE_DIR=/data/storage
VOLUME /data
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
