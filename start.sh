#!/bin/sh
set -eu
project_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ ! -x "$project_root/.venv/bin/python" ]; then
  echo 'Run ./setup.sh first.' >&2
  exit 1
fi
exec "$project_root/.venv/bin/python" "$project_root/scripts/run_app.py" start "$@"
