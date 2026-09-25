#!/usr/bin/env bash
# Cria .venv/ com as dependencias do backend, sem sudo.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv"

if [ ! -x "$VENV/bin/python" ]; then
  # --system-site-packages: o GTK/WebKit (python3-gi) vem do sistema.
  # --without-pip: o Ubuntu nao traz o ensurepip sem o python3-venv (que pede sudo).
  /usr/bin/python3 -m venv --system-site-packages --without-pip "$VENV"
fi

if ! "$VENV/bin/python" -m pip --version >/dev/null 2>&1; then
  curl -fsSL https://bootstrap.pypa.io/get-pip.py | "$VENV/bin/python" - --quiet
fi

"$VENV/bin/python" -m pip install --quiet -e "$ROOT/backend[dev]"

if ! "$VENV/bin/python" -c "import gi; gi.require_version('WebKit2', '4.1')" 2>/dev/null; then
  echo "Aviso: WebKitGTK 4.1 (gir1.2-webkit2-4.1) nao encontrado; os testes rodam, mas a janela do app nao abre." >&2
fi

echo "Ambiente pronto em .venv/"
