# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Runtime stage
FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .

ENV PYTHONPATH=/app

RUN chmod +x scripts/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["scripts/entrypoint.sh"]
