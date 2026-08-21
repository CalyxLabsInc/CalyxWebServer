#!/bin/sh
# Calyx Web Server installer
# Run from the project directory with: sudo sh install.sh

set -eu

PROGRAM_NAME="calyxserver"
INSTALL_DIR="/usr/local/bin"
INSTALL_PATH="${INSTALL_DIR}/${PROGRAM_NAME}"
CONFIG_DIR="/var/calyxserver/configuration"
CONFIG_PATH="${CONFIG_DIR}/config.calyx"
WEB_ROOT="/var/calyxserver/www"

fail() {
    printf '%s\n' "Installation failed: $*" >&2
    exit 1
}

if [ "$(id -u)" -ne 0 ]; then
    fail "this installer must be run as root. Try: sudo sh install.sh"
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SOURCE_FILE="${SCRIPT_DIR}/calyxserver.py"
PROJECT_CONFIG="${SCRIPT_DIR}/config.calyx"

[ -f "$SOURCE_FILE" ] || fail "calyxserver.py was not found next to install.sh"
command -v python3 >/dev/null 2>&1 || fail "Python 3 is required but was not found"

# Check the source before installing it.
python3 -m py_compile "$SOURCE_FILE" || fail "calyxserver.py did not pass Python syntax validation"

mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$WEB_ROOT"

# Install the Python program as a directly executable system command.
install -m 0755 "$SOURCE_FILE" "$INSTALL_PATH"

# Calyx 2.0 originally uses /var/calyxserver/config.calyx. Update the installed
# command so plain `calyxserver` uses the documented installation path.
python3 - "$INSTALL_PATH" "$CONFIG_PATH" <<'PY'
from pathlib import Path
import sys

program = Path(sys.argv[1])
config_path = sys.argv[2]
source = program.read_text(encoding="utf-8")
old = "DEFAULT_CONFIG=Path('/var/calyxserver/config.calyx')"
new = f"DEFAULT_CONFIG=Path({config_path!r})"
if old not in source:
    raise SystemExit(
        "Unable to set the installed configuration path. "
        "The expected DEFAULT_CONFIG declaration was not found."
    )
program.write_text(source.replace(old, new, 1), encoding="utf-8")
PY
chmod 0755 "$INSTALL_PATH"

# Preserve an existing installation's configuration. Otherwise install the
# project template, or let Calyx generate its built-in default configuration.
if [ ! -f "$CONFIG_PATH" ]; then
    if [ -f "$PROJECT_CONFIG" ]; then
        install -m 0644 "$PROJECT_CONFIG" "$CONFIG_PATH"
    else
        "$INSTALL_PATH" --config "$CONFIG_PATH" --check-config >/dev/null
    fi
fi

# Ensure the configured default website directory exists. Calyx will create
# its welcome page at startup without overwriting an existing index.html.
chmod 0755 /var/calyxserver "$CONFIG_DIR" "$WEB_ROOT"

# Validate exactly the configuration that the installed command will use.
"$INSTALL_PATH" --config "$CONFIG_PATH" --check-config >/dev/null || \
    fail "the installed configuration is invalid: $CONFIG_PATH"

printf '\n%s\n\n' "Installation complete. To customize reverse proxying, https settings and more, please edit the config file: /var/calyxserver/configuration/config.calyx. The default webpage is now live and actively being hosted by your machine, for more info on Calyx Web Server please visit localhost:8080 or whatever port you have set in the config file"
printf '%s\n' "Starting Calyx Web Server. Press Ctrl+C to stop it."

# Replace the installer process with the server process. This intentionally
# remains in the foreground so startup errors and request logs stay visible.
exec "$INSTALL_PATH" --config "$CONFIG_PATH"
