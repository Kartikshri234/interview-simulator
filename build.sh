#!/usr/bin/env bash
# build.sh — Render build script
set -o errexit

# Ensure setuptools (which provides pkg_resources) is installed first
# This is critical for Python 3.12+ where pkg_resources is no longer built-in
pip install --upgrade pip
pip install --upgrade setuptools wheel

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
