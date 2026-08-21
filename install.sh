#!/bin/sh
# Calyx Web Server Installer
# Run from the project directory with: sudo sh install.sh

set -eu

PROGRAM_NAME="calyxserver"
INSTALL_DIR="/usr/local/bin"
INSTALL_PATH="${INSTALL_DIR}/${PROGRAM_NAME}"
CONFIG_DIR="/var/calyxserver/configuration"
CONFIG_PATH="${CONFIG_DIR}/config.calyx"
WEB_ROOT="/var/calyxserver/www"
SYSTEMD_DIR="/etc/systemd/system"
SERVICE_NAME="calyxserver.service"
SERVICE_PATH="${SYSTEMD_DIR}/${SERVICE_NAME}"

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
PROJECT_SERVICE="${SCRIPT_DIR}/${SERVICE_NAME}"

[ -f "$SOURCE_FILE" ] || \
    fail "calyxserver.py was not found next to install.sh"
[ -f "$PROJECT_SERVICE" ] || \
    fail "${SERVICE_NAME} was not found next to install.sh"

command -v python3 >/dev/null 2>&1 || \
    fail "Python 3 is required but was not found"
command -v systemctl >/dev/null 2>&1 || \
    fail "systemd is required, but systemctl was not found"
command -v install >/dev/null 2>&1 || \
    fail "the install command was not found"

printf '%s\n' "Validating Calyx Web Server source code..."
python3 -m py_compile "$SOURCE_FILE" || \
    fail "calyxserver.py did not pass Python syntax validation"

printf '%s\n' "Creating Calyx Web Server directories..."
mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$WEB_ROOT" "$SYSTEMD_DIR"
chmod 0755 /var/calyxserver "$CONFIG_DIR" "$WEB_ROOT"

printf '%s\n' "Installing the calyxserver command..."
install -m 0755 "$SOURCE_FILE" "$INSTALL_PATH"

# Preserve an existing configuration. On a new installation, install the
# project template when available. Otherwise, ask Calyx to create its built-in
# default configuration at the correct location.
if [ -f "$CONFIG_PATH" ]; then
    printf '%s\n' "Preserving existing configuration: $CONFIG_PATH"
elif [ -f "$PROJECT_CONFIG" ]; then
    printf '%s\n' "Installing the default configuration..."
    install -m 0644 "$PROJECT_CONFIG" "$CONFIG_PATH"
else
    printf '%s\n' "Generating the default configuration..."
    "$INSTALL_PATH" --config "$CONFIG_PATH" --check-config >/dev/null || \
        fail "Calyx could not generate its default configuration"
fi

printf '%s\n' "Validating the active configuration..."
"$INSTALL_PATH" --config "$CONFIG_PATH" --check-config >/dev/null || \
    fail "the installed configuration is invalid: $CONFIG_PATH"

printf '%s\n' "Installing the systemd service..."
install -m 0644 "$PROJECT_SERVICE" "$SERVICE_PATH"

# Confirm that the installed service uses the same command and configuration
# paths prepared by this installer.
grep -Fq "ExecStart=${INSTALL_PATH} --config ${CONFIG_PATH}" "$SERVICE_PATH" || \
    fail "${SERVICE_NAME} does not use the expected executable and configuration paths"

printf '%s\n' "Reloading systemd..."
systemctl daemon-reload

printf '%s\n' "Enable Calyx Web Server at boot manually with sudo systemctl enable calyxserver"

printf '%s\n' "Starting Calyx Web Server..."
if systemctl is-active --quiet "$SERVICE_NAME"; then
    systemctl restart "$SERVICE_NAME"
else
    systemctl start "$SERVICE_NAME"
fi

if ! systemctl is-active --quiet "$SERVICE_NAME"; then
    printf '%s\n' "Calyx Web Server did not remain active after startup." >&2
    printf '%s\n' "Recent service logs:" >&2
    journalctl -u "$SERVICE_NAME" -n 30 --no-pager >&2 || true
    fail "unable to start ${SERVICE_NAME}"
fi

printf '\n%s\n\n' "Installation complete. To customize reverse proxying, https settings and more, please edit the config file: /var/calyxserver/configuration/config.calyx. The default webpage is now live and actively being hosted by your machine, for more info on Calyx Web Server please visit localhost:8080 or whatever port you have set in the config file"
printf '%s\n' "Calyx Web Server has been installed as the 'calyxserver' command."
printf '%s\n' "The calyxserver systemd service is active."
printf '%s\n' "To enable Calyx Web Server at boot you must manually run sudo systemctl enable calyxserver"
printf '%s\n' "Service status: sudo systemctl status calyxserver"
printf '%s\n' "Live logs: sudo journalctl -u calyxserver -f"
printf '%s\n' "Restart after configuration changes: sudo systemctl restart calyxserver"
