#!/bin/bash
set -e

# Stop and remove any old container
if [ "$(sudo docker ps -aq -f name=pokeparty)" ]; then
    echo "🧹 Removing old pokeparty container..."
    sudo docker stop pokeparty || true
    sudo docker rm pokeparty || true
fi

echo "🚀 Starting PokéParty container..."

# Run the container
sudo docker run -d \
    --name pokeparty \
    -p 80:5000 \
    -v $(pwd)/src:/app/src \
    pokeparty

echo "✅ PokéParty is running! Use: sudo docker logs -f pokeparty"

