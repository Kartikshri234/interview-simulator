#!/usr/bin/env bash
# build.sh — Render build script
set -o errexit

# Upgrade pip and core build tools first
pip install --upgrade pip setuptools wheel

# Install all dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations only if DATABASE_URL is set AND valid (contains postgresql)
if [[ "$DATABASE_URL" == postgres* ]] || [[ "$DATABASE_URL" == postgresql* ]]; then
    echo "DATABASE_URL found, running migrations..."
    python manage.py migrate --noinput
else
    echo "No valid DATABASE_URL, skipping migrations."
fi
