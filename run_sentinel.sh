#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# Set Chrome version to avoid SSL certificate issues during driver download
if [ -z "${CHROME_MAJOR_VERSION:-}" ]; then
  export CHROME_MAJOR_VERSION=139
  echo "Using Chrome version: $CHROME_MAJOR_VERSION"
fi

source venv/bin/activate
python main.py


