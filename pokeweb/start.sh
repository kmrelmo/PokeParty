#!/bin/bash
set -e

echo "🧹 Removing old pokeparty container (if any)..."
docker rm -f pokeparty 2>/dev/null || true

DB_PATH="/home/ubuntu/PokeParty/pokeweb/src/db.sqlite"

if [ ! -f "$DB_PATH" ]; then
  echo "⚠️ Database not found at $DB_PATH"
  echo "Creating new db.sqlite..."
  touch "$DB_PATH"
  chmod 666 "$DB_PATH"
fi

echo "🚀 Starting PokéParty container..."
docker run -d \
  --name pokeparty \
  -p 80:5000 \
  -v "$DB_PATH":/app/db.sqlite \
  pokeparty

echo "✅ PokéParty is running! View logs with: sudo docker logs -f pokeparty"