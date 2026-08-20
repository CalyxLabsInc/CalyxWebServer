# Calyx Web Server

Calyx Web Server is a small open-source static web server written entirely with the Python standard library. It has no third-party dependencies.

## Requirements

- Linux or another Unix-like system
- Python 3.10 or newer
- Root privileges when using `/var/calyxserver/www/` or a privileged port below 1024

## Quick start

```bash
unzip calyx-web-server-1.0.0.zip
cd calyx-web-server
sudo python3 calyxserver.py
```

Enter a port when prompted. The application creates `/var/calyxserver/www/`, adds a starter `index.html` if one does not exist, and serves the directory on all network interfaces.

Open `http://localhost:PORT/` in a browser, replacing `PORT` with the selected port.

## Command-line options

```text
--port PORT   Skip the interactive prompt
--host HOST   Bind address; default is 0.0.0.0
--root PATH   Public root; default is /var/calyxserver/www
--verbose     Enable debug logging
--version     Display the version
```

Example without root privileges:

```bash
python3 calyxserver.py --root "$HOME/calyx-www" --host 127.0.0.1 --port 8080
```

## Installing as a command

```bash
sudo install -m 0755 calyxserver.py /usr/local/bin/calyxserver
sudo calyxserver
```

## Testing

```bash
python3 -m unittest discover -s tests -v
```

## Scope and production note

Version 1.0.0 is a static-file server. It supports concurrent requests, MIME types, directory indexes, directory listings, request logging, and graceful shutdown. It does not implement reverse proxying, TLS termination, CGI, virtual hosts, caching, rate limiting, or the extensive hardening of nginx or Apache. For exposure to untrusted public internet traffic, place it behind a mature reverse proxy and run it under a dedicated, unprivileged account.

## License

MIT License. See `LICENSE`.
