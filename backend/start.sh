#!/usr/bin/env bash
set -e

FABRIC_PATH="$HOME/.local/bin/fabric"
FABRIC_ENV_DIR="$HOME/.config/fabric"

# --- Install fabric binary if missing ---
if ! command -v fabric &>/dev/null && [ ! -f "$FABRIC_PATH" ]; then
  echo "Installing fabric binary..."
  mkdir -p "$HOME/.local/bin"
  TMPDIR=$(mktemp -d)
  URL="https://github.com/danielmiessler/Fabric/releases/latest/download/fabric_Linux_x86_64.tar.gz"
  if command -v curl &>/dev/null; then
    curl -sSL "$URL" | tar xzf - -C "$TMPDIR"
  else
    wget -qO- "$URL" | tar xzf - -C "$TMPDIR"
  fi
  BIN=$(find "$TMPDIR" -type f -name 'fabric' | head -1)
  if [ -n "$BIN" ]; then
    cp "$BIN" "$HOME/.local/bin/fabric"
    chmod +x "$HOME/.local/bin/fabric"
    echo "fabric installed"
  else
    echo "Warning: fabric binary not found in archive"
  fi
  rm -rf "$TMPDIR"
fi

export PATH="$HOME/.local/bin:$PATH"

# --- Create fabric .env if missing ---
if [ ! -f "$FABRIC_ENV_DIR/.env" ] && [ -n "$OPENROUTER_API_KEY" ]; then
  echo "Creating fabric .env..."
  mkdir -p "$FABRIC_ENV_DIR"
  cat > "$FABRIC_ENV_DIR/.env" <<EOF
DEFAULT_VENDOR=${OPENROUTER_VENDOR:-OpenRouter}
DEFAULT_MODEL=${OPENROUTER_MODEL:-deepseek/deepseek-v4-flash}
OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
OPENROUTER_API_BASE_URL=https://openrouter.ai/api/v1
EOF
fi

exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"