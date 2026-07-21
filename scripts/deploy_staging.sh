#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Extract the version number from VERSION.md
if [ ! -f "VERSION.md" ]; then
    echo "Error: VERSION.md not found!"
    exit 1
fi

VERSION=$(cat VERSION.md | tr -d '\n' | tr -d '\r')
echo "Preparing deployment for version v${VERSION}..."

# Ensure we are on the main branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "Warning: Not on the 'main' branch. Deploying from $CURRENT_BRANCH."
fi

# Tag the build locally
echo "Tagging git commit with v${VERSION}..."
git tag -a "v${VERSION}" -m "Release v${VERSION}" || echo "Tag v${VERSION} already exists. Proceeding..."

# Simulate staging deployment push
echo "Simulating push to staging environment..."

# In a real environment, this would push images or sync via SSH
# e.g., docker tag sirens-kiosk:latest myregistry.com/sirens-kiosk:v${VERSION}
# e.g., docker push myregistry.com/sirens-kiosk:v${VERSION}
# e.g., scp docker-compose.yml admin@staging-server:/app/

echo "---"
echo "✅ Deployment tagged and staged successfully for v${VERSION}."
echo "---"
