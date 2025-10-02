# Build stage
FROM python:3.10-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn==20.1.0

# Production stage
FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn
COPY . .
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8080
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV USE_MEMORY_DB=0
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:create_app()"]