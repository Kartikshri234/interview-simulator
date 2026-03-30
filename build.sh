#!/usr/bin/env bash
# build.sh — Render build script
set -o errexit

echo "==> Python version: $(python --version)"

echo "==> Upgrading pip..."
pip install --upgrade pip

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Build complete."
