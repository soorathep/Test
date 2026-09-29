#!/bin/zsh
set -eu
cd "$(dirname "$0")"
"$HOME/.venvs/optim/bin/python" scripts/build_cases.py
"$HOME/.venvs/optim/bin/python" scripts/build_all.py
"$HOME/.venvs/optim/bin/python" scripts/verify_catalog.py
"${QUARTO_BIN:-$HOME/.local/opt/quarto/bin/quarto}" render

"$HOME/.venvs/optim/bin/python" scripts/link_chapters.py
