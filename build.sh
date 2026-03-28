#!/usr/bin/env bash
# build.sh — Render build script
set -o errexit

# Upgrade pip and core build tools first
pip install --upgrade pip setuptools wheel

# Install all dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations — only if DATABASE_URL is set
if [ -n "$DATABASE_URL" ]; then
    python manage.py migrate --noinput
fi
