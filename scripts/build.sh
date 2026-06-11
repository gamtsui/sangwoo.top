#!/bin/bash
# Incremental build script for Sangwoo.top frontend
# Only rebuilds pages affected by changed data
# Usage: ./scripts/build.sh [--full]

set -e

cd "$(dirname "$0")/../frontend"

API_BASE="${BUILD_API:-http://localhost:8000}"
CACHE_DIR=".build-cache"
FULL_BUILD="$([ "$1" = "--full" ] && echo "1" || echo "0")"

mkdir -p "$CACHE_DIR"

echo "=== Sangwoo.frontend build (API: $API_BASE) ==="

# Fetch current data hashes
fetch_hash() {
  local endpoint="$1"
  local label="$2"
  curl -sf "$API_BASE/api/$endpoint" 2>/dev/null | md5sum | awk '{print $1}' || echo "no-api-$label"
}

PRODUCTS_HASH=$(fetch_hash "products" "products")
NEWS_HASH=$(fetch_hash "news" "news")
ABOUT_HASH=$(fetch_hash "about" "about")
CONTACT_HASH=$(fetch_hash "contact" "contact")
SETTINGS_HASH=$(fetch_hash "settings" "settings")

# Load cached hashes
CACHE_FILE="$CACHE_DIR/last-build.txt"
if [ -f "$CACHE_FILE" ]; then
  source "$CACHE_FILE"
fi

# Detect changes
CHANGED=""
[ "$FULL_BUILD" = "1" ] && CHANGED="all"
[ -z "$CHANGED" ] && [ "$PRODUCTS_HASH" != "${CACHE_PRODUCTS_HASH:-}" ] && CHANGED="$CHANGED products"
[ -z "$CHANGED" ] && [ "$NEWS_HASH" != "${CACHE_NEWS_HASH:-}" ] && CHANGED="$CHANGED news"
[ -z "$CHANGED" ] && [ "$ABOUT_HASH" != "${CACHE_ABOUT_HASH:-}" ] && CHANGED="$CHANGED about"
[ -z "$CHANGED" ] && [ "$CONTACT_HASH" != "${CACHE_CONTACT_HASH:-}" ] && CHANGED="$CHANGED contact"
[ -z "$CHANGED" ] && [ "$SETTINGS_HASH" != "${CACHE_SETTINGS_HASH:-}" ] && CHANGED="$CHANGED settings"

if [ -z "$CHANGED" ]; then
  echo "No data changes detected. Skipping build."
  exit 0
fi

echo "Changes detected:$CHANGED"

# Export env for Astro
export BUILD_API="$API_BASE"

# Build
npm run build

# Save cache
cat > "$CACHE_FILE" << EOF
CACHE_PRODUCTS_HASH="$PRODUCTS_HASH"
CACHE_NEWS_HASH="$NEWS_HASH"
CACHE_ABOUT_HASH="$ABOUT_HASH"
CACHE_CONTACT_HASH="$CONTACT_HASH"
CACHE_SETTINGS_HASH="$SETTINGS_HASH"
CACHE_TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
EOF

echo "=== Build complete ==="
