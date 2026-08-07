#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
VENV_DIR="${PROJECT_ROOT}/.venv"
PYPROJECT_FILE="${BACKEND_DIR}/pyproject.toml"
INSTALL_MARKER="${VENV_DIR}/.dependencies-installed"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

uvicorn_args=("$@")
for ((index = 0; index < ${#uvicorn_args[@]}; index++)); do
  case "${uvicorn_args[index]}" in
    --host)
      if ((index + 1 < ${#uvicorn_args[@]})); then
        HOST="${uvicorn_args[index + 1]}"
      fi
      ;;
    --host=*) HOST="${uvicorn_args[index]#--host=}" ;;
    --port)
      if ((index + 1 < ${#uvicorn_args[@]})); then
        PORT="${uvicorn_args[index + 1]}"
      fi
      ;;
    --port=*) PORT="${uvicorn_args[index]#--port=}" ;;
  esac
done

if [[ ! "${PORT}" =~ ^[0-9]+$ ]] || ((PORT < 1 || PORT > 65535)); then
  echo "Error: PORT must be an integer between 1 and 65535 (received: ${PORT})." >&2
  exit 1
fi

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

if ! "${PYTHON_BIN}" - "${HOST}" "${PORT}" <<'PY'
import socket
import sys

host, port_text = sys.argv[1:]
port = int(port_text)
probe_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host

try:
    addresses = socket.getaddrinfo(probe_host, port, type=socket.SOCK_STREAM)
except socket.gaierror as error:
    raise SystemExit(f"Error: Cannot resolve host {host!r}: {error}") from error

available = False
for family, sock_type, protocol, _, address in addresses:
    with socket.socket(family, sock_type, protocol) as probe:
        try:
            probe.bind(address)
        except OSError:
            continue
        available = True
        break

raise SystemExit(0 if available else 1)
PY
then
  echo "Error: ${HOST}:${PORT} is already in use." >&2
  echo "Stop the existing process, or choose another port, for example:" >&2
  echo "  ./run.sh --port 8080" >&2
  echo "  PORT=8080 ./run.sh" >&2
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

display_host="${HOST}"
if [[ "${display_host}" == "0.0.0.0" || "${display_host}" == "::" ]]; then
  display_host="localhost"
fi

echo "Starting the application at http://${display_host}:${PORT}"
cd "${BACKEND_DIR}"
uvicorn_command=(
  "${VENV_DIR}/bin/uvicorn"
  app.main:app
  --reload
  --host "${HOST}"
  --port "${PORT}"
)
if ((${#uvicorn_args[@]} > 0)); then
  uvicorn_command+=("${uvicorn_args[@]}")
fi
exec "${uvicorn_command[@]}"
