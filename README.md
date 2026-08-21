# Calyx Web Server

Welcome to **Calyx Web Server**, an open-source, lightweight, and approachable web server created by **Calyx Labs Inc.** Calyx is written in pure Python and is designed to provide a simple alternative to larger web server platforms such as Nginx and Apache.

Calyx can host static websites directly, provide HTTPS, apply configurable security controls, and act as a reverse-proxy gateway for separately running web applications. Its readable source code and centralized configuration make it suitable for developers, self-hosters, test environments, home servers, and lightweight production deployments.

## Features

- Pure Python implementation using the Python standard library
- Static website hosting from a configurable document root
- Automatic default website creation
- Central configuration through `config.calyx`
- HTTP and HTTPS support
- Configurable TLS certificate and private key paths
- Configurable minimum TLS version
- Path-based reverse proxy routes
- Application-layer rate limiting and temporary client bans
- IPv4 and IPv6 allow and deny rules
- Request-body size limits
- Request timeouts
- Configurable HTTP method restrictions
- Safer default response headers
- Content Security Policy support
- HTTP Strict Transport Security when HTTPS is enabled
- Directory traversal and symbolic-link escape protection
- Concurrent request handling
- Graceful shutdown
- Configuration validation
- Command-line installation as `calyxserver`

## Requirements

Before installing Calyx Web Server, make sure the system has:

- A Linux operating system
- Python 3.10 or newer
- Root or `sudo` access for system-wide installation
- An available network port, with port `8080` used by default

Calyx does not require third-party Python packages.

## Installation and First Start

Download or clone the project, then enter the project directory:

```bash
cd CalyxWebServer-main
```

Make the installer executable:

```bash
chmod +x install.sh
```

Run the installer:

```bash
sudo bash ./install.sh
```

The installer will:

1. Validate `calyxserver.py`.
2. Install Calyx as `/usr/local/bin/calyxserver`.
3. Create the Calyx application directories.
4. Install or create the main configuration file.
5. Preserve an existing configuration and website during reinstallation.
6. Create the default website directory.
7. Validate the active configuration.
8. Start Calyx Web Server.

The server runs in the foreground after installation. Press `Ctrl+C` when you want to stop it.

Once started, open the default website in a browser:

```text
http://localhost:8080
```

If you changed the port in `config.calyx`, replace `8080` with the configured port.

## Starting Calyx After Installation

The installer adds Calyx to the system as a command. Further starts only require:

```bash
sudo calyxserver
```

If the configured port is above `1023` and the configured files are accessible to your user, Calyx can be run without root privileges:

```bash
calyxserver
```

For production use, running Calyx under a dedicated, unprivileged service account is strongly recommended.

## Starting Calyx Automatically at Boot

If the Calyx package includes and installs the `calyxserver.service` systemd unit, enable automatic startup with:

```bash
sudo systemctl enable calyxserver
```

To enable the service and start it immediately:

```bash
sudo systemctl enable --now calyxserver
```

Useful service-management commands include:

```bash
sudo systemctl start calyxserver
sudo systemctl stop calyxserver
sudo systemctl restart calyxserver
sudo systemctl status calyxserver
```

View service logs with:

```bash
sudo journalctl -u calyxserver -f
```

> **Important:** `systemctl enable calyxserver` requires a `calyxserver.service` unit to be installed under a systemd unit directory. If your release does not include that unit yet, start Calyx manually with `sudo calyxserver` until the service file is installed.

## File Locations

The standard installation uses these locations:

```text
/usr/local/bin/calyxserver
/var/calyxserver/configuration/config.calyx
/var/calyxserver/www/
```

The default website is located at:

```text
/var/calyxserver/www/index.html
```

Replace the generated page with your own HTML, CSS, JavaScript, images, and other public website assets.

## Configuration

The main configuration file is:

```text
/var/calyxserver/configuration/config.calyx
```

Open it with:

```bash
sudo nano /var/calyxserver/configuration/config.calyx
```

After changing the configuration, restart Calyx:

```bash
sudo systemctl restart calyxserver
```

If Calyx is running manually, stop it with `Ctrl+C` and start it again:

```bash
sudo calyxserver
```

Validate the configuration without starting the server:

```bash
sudo calyxserver   --config /var/calyxserver/configuration/config.calyx   --check-config
```

## Hosting a Static Website

For normal static website hosting, leave reverse proxying disabled:

```ini
[proxy]
enabled = false
```

Calyx will serve files from the configured working directory:

```ini
[server]
working_directory = /var/calyxserver/www
```

For example, a request for:

```text
http://localhost:8080/about.html
```

will serve:

```text
/var/calyxserver/www/about.html
```

## HTTPS

To enable HTTPS, provide a valid certificate and private key:

```ini
[https]
enabled = true
certificate_file = /etc/calyxserver/tls/fullchain.pem
private_key_file = /etc/calyxserver/tls/privkey.pem
minimum_tls = 1.2
```

Protect the private key so that only the Calyx service account can read it. Calyx should fail safely rather than starting HTTPS with a missing certificate or key.

## Reverse Proxying

Reverse proxying allows Calyx to receive a request and forward it to a separately running HTTP application.

Example:

```ini
[proxy]
enabled = true
/api = http://127.0.0.1:9000
connect_timeout_seconds = 5
preserve_host = false
forwarded_headers = true
```

With this configuration:

```text
http://localhost:8080/api/users
```

is forwarded to the application listening on:

```text
http://127.0.0.1:9000/users
```

The upstream application must already be running. Enabling a proxy route does not open or start the upstream port.

For customers who only host files from `/var/calyxserver/www`, reverse proxying should remain disabled.

## Security and Production Use

Calyx includes several application-level hardening controls, but secure deployment also depends on the operating system, network, permissions, certificates, and deployment architecture.

Recommended production practices include:

- Run Calyx as a dedicated, unprivileged user.
- Keep Python and the operating system updated.
- Use HTTPS with a valid certificate.
- Restrict private-key file permissions.
- Enable only the HTTP methods the application requires.
- Keep directory listing disabled unless it is intentionally needed.
- Configure appropriate request and connection limits.
- Allow reverse-proxy access only to trusted upstream services.
- Do not trust forwarded client headers unless every direct connection comes from a trusted proxy.
- Monitor application and system logs.
- Use a firewall, load balancer, CDN, or specialist mitigation service for network-level denial-of-service protection.
- Back up the configuration and website before major upgrades.

Calyx rate limiting can reduce some application-layer abuse, but it cannot stop a volumetric attack that saturates the host or network connection before requests reach the application.

## Testing

Run the included automated tests from the project directory:

```bash
python3 -m unittest discover -s tests -v
```

Validate the Python source directly with:

```bash
python3 -m py_compile calyxserver.py
```

## Updating Calyx

Before installing a newer release, back up:

```text
/var/calyxserver/configuration/config.calyx
/var/calyxserver/www/
```

Run the newer release's installer from its project directory:

```bash
sudo ./install.sh
```

The installer is designed to preserve existing configuration files and website content. Review the changelog for new settings that may need to be added manually.

## Contributing

Contributions, bug reports, documentation improvements, security reviews, and feature proposals are welcome. Please keep changes readable, dependency-conscious, documented, and consistent with the goal of providing an approachable pure-Python web server.

When reporting a problem, include:

- Calyx Web Server version
- Python version
- Operating system and version
- Relevant configuration with private information removed
- Steps required to reproduce the issue
- Relevant error messages or logs

Do not publish private keys, passwords, authentication tokens, private IP information, or other secrets in an issue report.

## Donations

If you would like to support the continued development of Calyx Web Server and other Calyx Labs Inc. open-source projects, donations can be sent to the following addresses. Replace these placeholders with the official project addresses before publishing:

```text
Monero (XMR):   YOUR_MONERO_ADDRESS_HERE
Bitcoin (BTC):  YOUR_BITCOIN_ADDRESS_HERE
Litecoin (LTC): YOUR_LITECOIN_ADDRESS_HERE
```

Always verify donation addresses through an official Calyx Labs Inc. channel before sending funds.

## License

Calyx Web Server is open-source software distributed under the MIT License. See the `LICENSE` file for the complete license text.

---

**Copyright © 2026 Calyx Labs Inc. All rights reserved.**

Calyx Web Server is open-source software. Rights granted under the project's MIT License remain subject to the terms contained in the `LICENSE` file.
