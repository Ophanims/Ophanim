#!/bin/sh
set -eu
project_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ ! -x "$project_root/.venv/bin/python" ]; then
  echo 'No local virtual environment; nothing to stop.'
  exit 0
fi
exec "$project_root/.venv/bin/python" "$project_root/scripts/run_app.py" stop
