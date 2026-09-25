#!/usr/bin/env bash
# Gera build/sparksDB-<versao>-x86_64.AppImage. Rode depois de `npm run build:vite`.
# O AppImage usa o python3, o GTK 3 e o WebKitGTK 4.1 do sistema (Ubuntu Desktop 24.04+)
# e embute so as dependencias Python do backend.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
PYTHON_VERSIONS="3.12 3.13 3.14"
APPIMAGETOOL_VERSION="1.9.1"
VERSION="$(node -p "require('$ROOT/package.json').version")"

BUILD="$ROOT/build/appimage"
APPDIR="$BUILD/AppDir"
LIB="$APPDIR/usr/lib/sparksdb"
TOOL="$ROOT/build/tools/appimagetool-$APPIMAGETOOL_VERSION"
OUT="$ROOT/build/sparksDB-${VERSION}-x86_64.AppImage"

if [ ! -f "$ROOT/dist/index.html" ]; then
  echo "dist/index.html nao existe; rode 'npm run build:vite' antes." >&2
  exit 1
fi

rm -rf "$BUILD"
mkdir -p "$LIB/vendor" "$BUILD/wheels" "$(dirname "$TOOL")"

cp -r "$ROOT/backend/sparksdb" "$LIB/sparksdb"
cp -r "$ROOT/dist" "$LIB/dist"

mapfile -t DEPS < <("$PYTHON" -c "import tomllib; print('\n'.join(tomllib.load(open('$ROOT/backend/pyproject.toml', 'rb'))['project']['dependencies']))")

# proxy_tools (dependencia do pywebview) so existe como sdist; vira um wheel puro local.
"$PYTHON" -m pip wheel --quiet --no-deps -w "$BUILD/wheels" proxy_tools

# psycopg-binary e cffi sao compilados por versao do Python. Instala uma copia por
# versao e junta tudo: os .so levam a versao no nome e convivem no mesmo diretorio.
for v in $PYTHON_VERSIONS; do
  "$PYTHON" -m pip install --quiet --target "$BUILD/vendor-$v" \
    --only-binary=:all: --find-links "$BUILD/wheels" \
    --python-version "$v" --implementation cp \
    --platform manylinux_2_28_x86_64 --platform manylinux_2_17_x86_64 --platform manylinux2014_x86_64 \
    "${DEPS[@]}"
  cp -r --update=none "$BUILD/vendor-$v/." "$LIB/vendor/"
done
rm -rf "$LIB/vendor/bin"
find "$LIB" -name __pycache__ -prune -exec rm -rf {} +

cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
export PYTHONPATH="$HERE/usr/lib/sparksdb:$HERE/usr/lib/sparksdb/vendor"
export SPARKSDB_DIST="$HERE/usr/lib/sparksdb/dist"
# -P: nao poe a pasta atual no sys.path (um json.py qualquer ali quebraria o app).
exec /usr/bin/python3 -P -m sparksdb "$@"
EOF
chmod 755 "$APPDIR/AppRun"

cat > "$APPDIR/sparksdb.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=sparksDB
Comment=Cliente Postgres desktop
Exec=sparksdb
Icon=sparksdb
Categories=Development;Database;
Terminal=false
EOF
cp "$ROOT/backend/sparksdb/icon.png" "$APPDIR/sparksdb.png"

if [ ! -x "$TOOL" ]; then
  curl -fsSL -o "$TOOL" \
    "https://github.com/AppImage/appimagetool/releases/download/$APPIMAGETOOL_VERSION/appimagetool-x86_64.AppImage"
  chmod +x "$TOOL"
fi

# --appimage-extract-and-run: roda o appimagetool sem FUSE (necessario na CI).
ARCH=x86_64 "$TOOL" --appimage-extract-and-run "$APPDIR" "$OUT"
echo "Gerado: $OUT"
