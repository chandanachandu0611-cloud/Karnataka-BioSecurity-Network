#!/bin/bash
set -e
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"
echo "Starting Karnataka Biosecurity Network..."
echo "Initializing database (if first run)..."
python backend/app.py
