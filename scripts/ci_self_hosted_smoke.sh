#!/usr/bin/env bash
set -euo pipefail

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required"
  exit 1
fi
if ! command -v tar >/dev/null 2>&1; then
  echo "tar is required"
  exit 1
fi

GITLEAKS_VERSION="${GITLEAKS_VERSION:-8.24.2}"
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"
case "$ARCH" in
  x86_64) ARCH="x64" ;;
  arm64|aarch64) ARCH="arm64" ;;
  *) echo "Unsupported architecture: $ARCH" && exit 1 ;;
esac
case "$OS" in
  darwin|linux) ;;
  *) echo "Unsupported OS: $OS" && exit 1 ;;
esac

ASSET="gitleaks_${GITLEAKS_VERSION}_${OS}_${ARCH}.tar.gz"
URL="https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/${ASSET}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

curl -fsSL "$URL" -o "$TMP_DIR/gitleaks.tar.gz"
tar -xzf "$TMP_DIR/gitleaks.tar.gz" -C "$TMP_DIR"
"$TMP_DIR/gitleaks" dir . --redact --exit-code 1

echo "Self-hosted CI secret scan smoke passed."
