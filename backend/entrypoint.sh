#!/bin/sh
set -e

echo "⏳ Waiting for Postgres..."
until python -c "
import asyncio, asyncpg, os
async def check():
    url = os.getenv('DATABASE_URL','').replace('postgresql+asyncpg','postgresql')
    await asyncpg.connect(url)
asyncio.run(check())
" 2>/dev/null; do
  sleep 1
done

echo "✓ Postgres ready"
echo "🌱 Running seed..."
python seed.py

echo "🚀 Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
