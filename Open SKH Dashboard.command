#!/bin/zsh

# Double-click this file in Finder to inspect the website and open the
# private maintenance dashboard. Generated output stays in .maintenance/.

set -u

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

PYTHON_BIN="$(command -v python3 2>/dev/null || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  osascript -e 'display dialog "SKH Dashboard needs Python 3, but Python 3 was not found on this Mac." buttons {"OK"} default button "OK" with icon stop'
  exit 1
fi

RUNTIME_DIR="$SCRIPT_DIR/.maintenance/python"
if ! "$PYTHON_BIN" -c 'import yaml' >/dev/null 2>&1; then
  mkdir -p "$RUNTIME_DIR"
  echo "First run: preparing the YAML reader..."
  if ! "$PYTHON_BIN" -m pip install --quiet --disable-pip-version-check --target "$RUNTIME_DIR" PyYAML; then
    osascript -e 'display dialog "The Dashboard could not install its YAML reader. Check your internet connection and try again." buttons {"OK"} default button "OK" with icon stop'
    exit 1
  fi
fi

echo "Checking the SKH Research Group website..."
if [[ -d "$RUNTIME_DIR" ]]; then
  env PYTHONPATH="$RUNTIME_DIR" "$PYTHON_BIN" tools/maintenance/build_dashboard.py
else
  "$PYTHON_BIN" tools/maintenance/build_dashboard.py
fi
STATUS=$?

if [[ $STATUS -ne 0 ]]; then
  osascript -e 'display dialog "The Dashboard could not finish its checks. The Terminal window contains the details." buttons {"OK"} default button "OK" with icon stop'
  echo
  echo "Press any key to close this window."
  read -k 1
  exit $STATUS
fi

REPORT_FILE="$SCRIPT_DIR/.maintenance/dashboard.html"
if open "$REPORT_FILE" 2>/dev/null || open -a Safari "$REPORT_FILE" 2>/dev/null; then
  echo "Dashboard opened. You may close this Terminal window."
else
  osascript -e 'display dialog "The Dashboard report was created, but macOS could not open a browser. Open .maintenance/dashboard.html from the repository." buttons {"OK"} default button "OK" with icon caution'
  echo "Dashboard created at: $REPORT_FILE"
fi
sleep 2
