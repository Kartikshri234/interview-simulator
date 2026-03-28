#!/usr/bin/env bash
# build.sh — Render build script
set -o errexit

# Ensure setuptools/pkg_resources are available before anything else
pip install --upgrade pip setuptools wheel

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
