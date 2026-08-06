#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
VENV_DIR="${PROJECT_ROOT}/.venv"
PYPROJECT_FILE="${BACKEND_DIR}/pyproject.toml"
INSTALL_MARKER="${VENV_DIR}/.dependencies-installed"

if command -v python3.12 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3.12)"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  echo "Error: Python 3.12 or newer is required." >&2
  exit 1
fi

if ! "${PYTHON_BIN}" -c 'import sys; raise SystemExit(sys.version_info < (3, 12))'; then
  echo "Error: Python 3.12 or newer is required (found $("${PYTHON_BIN}" --version 2>&1))." >&2
  exit 1
fi

if [[ ! -f "${PROJECT_ROOT}/.env" ]]; then
  cp "${PROJECT_ROOT}/.env.example" "${PROJECT_ROOT}/.env"
  echo "Created .env from .env.example"
fi

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  echo "Creating Python virtual environment..."
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

if [[ ! -f "${INSTALL_MARKER}" || "${PYPROJECT_FILE}" -nt "${INSTALL_MARKER}" ]]; then
  echo "Installing backend dependencies..."
  "${VENV_DIR}/bin/python" -m pip install -e "${BACKEND_DIR}[dev]"
  touch "${INSTALL_MARKER}"
fi

echo "Starting the application at http://localhost:8000"
cd "${BACKEND_DIR}"
exec "${VENV_DIR}/bin/uvicorn" app.main:app --reload "$@"
