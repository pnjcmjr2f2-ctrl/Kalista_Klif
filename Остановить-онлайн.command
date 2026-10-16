#!/bin/zsh
set -eu
cd "$(dirname "$0")"
exec ../work/venv/bin/python kalista_online.py stop
