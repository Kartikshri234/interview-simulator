#!/usr/bin/env bash
# build.sh — Render build script
set -o errexit

# Fix pkg_resources missing on Python 3.14
pip install --upgrade pip setuptools wheel

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
