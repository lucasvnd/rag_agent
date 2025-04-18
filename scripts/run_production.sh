#!/bin/bash

# Load environment variables
set -a
source .env
set +a

# Check if running with Cloudflare Tunnel
if [ -z "$CLOUDFLARE_TUNNEL" ]; then
    echo "Warning: CLOUDFLARE_TUNNEL not set"
fi

# Start the FastAPI application with uvicorn
exec uvicorn app.main:app \
    --host ${HOST:-0.0.0.0} \
    --port ${PORT:-8000} \
    --workers ${WORKERS:-4} \
    --log-level ${LOG_LEVEL:-info} \
    --proxy-headers \
    --forwarded-allow-ips='*' 