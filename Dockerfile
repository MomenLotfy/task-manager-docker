
FROM python:3.11-alpine AS builder

WORKDIR /app

RUN apk add --no-cache gcc musl-dev libpq-dev

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-alpine

WORKDIR /app

RUN apk add --no-cache libpq wget

COPY --from=builder /install /usr/local

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

COPY . .

RUN chown -R appuser:appgroup /app

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD wget -qO- http://localhost:8000/api/health || exit 1

EXPOSE 8000

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "flask_app:app"]
