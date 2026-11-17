#!/bin/sh
set -eu
project_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$project_root"
case "${1:-}" in
  ''|--ml) ;;
  *) echo 'Usage: ./setup.sh [--ml]' >&2; exit 1 ;;
esac
if [ ! -x .venv/bin/python ]; then
  python3.12 -m venv .venv
fi
.venv/bin/python -m pip install -r backend/requirements.txt
if [ "${1:-}" = '--ml' ]; then
  .venv/bin/python -m pip install -r backend/requirements-ml.txt
fi
npm --prefix frontend ci
