#!/bin/zsh
set -eu
cd "$(dirname "$0")"
"$HOME/.venvs/optim/bin/python" scripts/build_cases.py
"${QUARTO_BIN:-$HOME/.local/opt/quarto/bin/quarto}" render
