# Installing Calyx Web Server

Welcome to **Calyx Web Server**, an open-source, lightweight web server created by **Calyx Labs Inc.** This guide explains how to install Calyx as a system command, start the server, enable automatic startup, and verify the installation.

## What the Installer Does

The included `install.sh` script performs the system-wide installation of Calyx Web Server. It:

- Validates the `calyxserver.py` source file.
- Installs Calyx as `/usr/local/bin/calyxserver`.
- Creates the Calyx configuration and website directories.
- Installs or generates the main `config.calyx` file.
- Preserves an existing configuration during reinstallation or upgrades.
- Preserves existing website files.
- Installs `calyxserver.service` as a systemd service.
- Reloads systemd so the new service is recognized.
- Starts or restarts Calyx Web Server.
- Confirms whether the service started successfully.

The installer **does not enable Calyx to start automatically at boot**. Automatic startup must be enabled manually after installation.

## Requirements

Before installing Calyx Web Server, make sure the system has:

- A Linux distribution using systemd
- Python 3.10 or newer
- The standard `install` command
- Root access or permission to use `sudo`
- An available TCP port, with port `8080` used by default

Check Python before proceeding:

```bash
python3 --version
```

Check that systemd is available:

```bash
systemctl --version
```

Calyx is built with the Python standard library and does not require third-party Python packages.

## Required Installation Files

Place the following files together in the same directory:

```text
calyxserver.py
calyxserver.service
config.calyx
install.sh
```

The installer searches for these files relative to its own location. Do not move `install.sh` into a different directory before running it unless the other required files are moved with it.

The project may also contain:

```text
README.md
CHANGELOG.md
INSTALLATION.md
LICENSE
tests/
```

These additional files are useful for documentation, release history, licensing, and testing, but they are not all required by the installer.

## Install Calyx Web Server

Open a terminal and change into the extracted or cloned project directory:

```bash
cd /path/to/calyx-web-server
```

Make the installer executable:

```bash
chmod +x install.sh
```

Run the installer with root privileges:

```bash
sudo ./install.sh
```

You may alternatively run it through a compatible shell:

```bash
sudo sh install.sh
```

The installer will display progress while it validates the source, creates directories, installs the command and service, validates the configuration, and starts the server.

When installation finishes, it will remind you that automatic startup has not been enabled:

```text
you must enable calyxserver to start at boot by manually running sudo systemctl enable calyxserver
```

## Open the Default Website

Calyx listens on port `8080` by default. On the machine running Calyx, open:

```text
http://localhost:8080
```

You can also test it from a terminal:

```bash
curl -I http://localhost:8080
```

If you changed the configured port, replace `8080` with that port.

To access Calyx from another device, use the server's hostname or IP address:

```text
http://SERVER_ADDRESS:8080
```

Remote access also depends on the Calyx bind address, host firewall, router, cloud firewall, and network configuration.

## Enable Calyx at Boot

The installer installs the systemd service but intentionally does not enable automatic startup.

To make Calyx start whenever the machine boots, run:

```bash
sudo systemctl enable calyxserver
```

This enables future boot startup. It does not necessarily restart the currently running service.

To enable boot startup and start Calyx immediately in one command, use:

```bash
sudo systemctl enable --now calyxserver
```

Confirm whether automatic startup is enabled:

```bash
sudo systemctl is-enabled calyxserver
```

The expected result is:

```text
enabled
```

## Start Calyx Manually

After installation, Calyx is available as a system command:

```bash
sudo calyxserver
```

However, when using the installed systemd service, service-management commands are recommended so that logs, restarts, and process state remain under systemd control.

Start the service:

```bash
sudo systemctl start calyxserver
```

Stop the service:

```bash
sudo systemctl stop calyxserver
```

Restart the service:

```bash
sudo systemctl restart calyxserver
```

Check its current status:

```bash
sudo systemctl status calyxserver
```

Do not run `sudo calyxserver` while the systemd service is already active on the same port. The second process will fail because the configured port is already in use.

## View Server Logs

View recent Calyx service logs:

```bash
sudo journalctl -u calyxserver --no-pager
```

Follow new log entries in real time:

```bash
sudo journalctl -u calyxserver -f
```

View logs from the current boot only:

```bash
sudo journalctl -u calyxserver -b
```

Press `Ctrl+C` to stop following live logs. This does not stop the server.

## Installed File Locations

The standard installation uses the following paths:

```text
/usr/local/bin/calyxserver
/etc/systemd/system/calyxserver.service
/var/calyxserver/configuration/config.calyx
/var/calyxserver/www/
```

The installed command is:

```text
/usr/local/bin/calyxserver
```

The active system configuration is:

```text
/var/calyxserver/configuration/config.calyx
```

The default public website directory is:

```text
/var/calyxserver/www/
```

The default homepage is:

```text
/var/calyxserver/www/index.html
```

## Customize the Website

Replace the generated homepage with your own site files:

```bash
sudo nano /var/calyxserver/www/index.html
```

You can place HTML, CSS, JavaScript, images, downloads, and other static files inside:

```text
/var/calyxserver/www/
```

Calyx preserves an existing `index.html` during startup and reinstallation.

## Edit the Server Configuration

Open the active configuration file:

```bash
sudo nano /var/calyxserver/configuration/config.calyx
```

The configuration controls settings such as:

- Listening host and port
- Static website working directory
- Index filenames
- Directory listing
- HTTPS certificate and private key
- Minimum TLS version
- Reverse-proxy routes
- Request timeouts
- Maximum request-body size
- Rate limiting and temporary bans
- IPv4 and IPv6 access rules
- Allowed HTTP methods
- Security headers

After editing the configuration, validate it:

```bash
sudo calyxserver \
  --config /var/calyxserver/configuration/config.calyx \
  --check-config
```

If validation succeeds, restart the service:

```bash
sudo systemctl restart calyxserver
```

Then confirm that it remains active:

```bash
sudo systemctl status calyxserver
```

## Change the Listening Port

Open the configuration:

```bash
sudo nano /var/calyxserver/configuration/config.calyx
```

Find the `[server]` section and change the port:

```ini
[server]
host = 0.0.0.0
port = 8080
```

For example, to use port `8000`:

```ini
port = 8000
```

Validate and restart Calyx:

```bash
sudo calyxserver \
  --config /var/calyxserver/configuration/config.calyx \
  --check-config
sudo systemctl restart calyxserver
```

Visit the updated address:

```text
http://localhost:8000
```

Ports below `1024` may require additional service permissions or capabilities. Review the systemd service and deployment security before changing Calyx to port `80` or `443`.

## Static Hosting and Reverse Proxying

For normal static hosting from `/var/calyxserver/www`, leave reverse proxying disabled:

```ini
[proxy]
enabled = false
```

Enable reverse proxying only when Calyx must forward matching requests to a separate HTTP application that is already running.

Example:

```ini
[proxy]
enabled = true
/api = http://127.0.0.1:9000
connect_timeout_seconds = 5
preserve_host = false
forwarded_headers = true
```

In that example, Calyx continues serving ordinary website files, but requests beginning with `/api` are sent to the separate application listening on port `9000`.

A reverse-proxy setting does not start the upstream application and does not create an additional listening port.

## HTTPS Setup

Set the certificate and private key in the `[https]` section:

```ini
[https]
enabled = true
certificate_file = /etc/calyxserver/tls/fullchain.pem
private_key_file = /etc/calyxserver/tls/privkey.pem
minimum_tls = 1.2
```

Make sure the certificate and private key exist and are readable by the account running Calyx. Protect the private key from other users.

After changing HTTPS settings:

```bash
sudo calyxserver \
  --config /var/calyxserver/configuration/config.calyx \
  --check-config
sudo systemctl restart calyxserver
```

If startup fails, inspect the logs:

```bash
sudo journalctl -u calyxserver -n 50 --no-pager
```

## Upgrade an Existing Installation

Before upgrading, back up the active configuration and website:

```bash
sudo cp /var/calyxserver/configuration/config.calyx \
  /var/calyxserver/configuration/config.calyx.backup
sudo cp -a /var/calyxserver/www \
  /var/calyxserver/www.backup
```

Download or extract the newer release, enter its directory, and run:

```bash
chmod +x install.sh
sudo ./install.sh
```

The installer is designed to preserve the existing active configuration and website files. It replaces the installed Calyx command and systemd service with the versions included in the new release.

Because the installer does not enable the service automatically, verify its boot setting after an upgrade:

```bash
sudo systemctl is-enabled calyxserver
```

If the service is disabled and you want boot startup, run:

```bash
sudo systemctl enable calyxserver
```

Review `CHANGELOG.md` for new configuration options or upgrade notes.

## Troubleshooting

### Permission denied while running the installer

Run the installer with `sudo`:

```bash
sudo ./install.sh
```

### `calyxserver.py` was not found

Make sure these files are in the same directory:

```text
install.sh
calyxserver.py
calyxserver.service
config.calyx
```

### `calyxserver.service` was not found

Download or restore the service file and place it next to `install.sh`, then rerun the installer.

### The service does not start

Check its status:

```bash
sudo systemctl status calyxserver
```

Read recent logs:

```bash
sudo journalctl -u calyxserver -n 50 --no-pager
```

Validate the configuration:

```bash
sudo calyxserver \
  --config /var/calyxserver/configuration/config.calyx \
  --check-config
```

### The configured port is already in use

Find the process using port `8080`:

```bash
sudo ss -ltnp | grep ':8080'
```

Stop the conflicting application or select another port in `config.calyx`.

### The website works locally but not remotely

Check that:

- The configured host is `0.0.0.0` or the desired network address.
- The host firewall permits the configured port.
- Any router or cloud firewall permits the connection.
- The client uses the server's actual hostname or IP address, not `localhost`.

### Calyx does not start after reboot

Confirm that the service is enabled:

```bash
sudo systemctl is-enabled calyxserver
```

If the result is `disabled`, enable it:

```bash
sudo systemctl enable calyxserver
```

Then start it:

```bash
sudo systemctl start calyxserver
```

## Optional Manual Removal

Stop and disable the service:

```bash
sudo systemctl disable --now calyxserver
```

Remove the installed command and service:

```bash
sudo rm -f /usr/local/bin/calyxserver
sudo rm -f /etc/systemd/system/calyxserver.service
sudo systemctl daemon-reload
```

The following command permanently removes the configuration and all hosted website files:

```bash
sudo rm -rf /var/calyxserver
```

Back up any important configuration or website content before removing that directory.

## Installation Checklist

After installation, verify the following:

- `calyxserver` is available as a command.
- `calyxserver.service` is installed.
- The active configuration passes validation.
- `systemctl status calyxserver` reports an active service.
- The default website opens on the configured port.
- Automatic startup is enabled manually if desired.
- HTTPS and firewall settings are configured appropriately for production.

To enable automatic startup now, run:

```bash
sudo systemctl enable calyxserver
```

---

**Copyright © 2026 Calyx Labs Inc. All rights reserved.**

Calyx Web Server is distributed under the terms provided in the project's `LICENSE` file.
