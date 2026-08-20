#!/usr/bin/env python3
"""Calyx Web Server: a small, dependency-free static HTTP server."""

from __future__ import annotations

import argparse
import html
import logging
import mimetypes
import os
import posixpath
import signal
import sys
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

__version__ = "1.0.0"
DEFAULT_ROOT = Path("/var/calyxserver/www")
DEFAULT_HOST = "0.0.0.0"
SERVER_NAME = f"CalyxWebServer/{__version__}"
WELCOME_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Calyx Lab's Open-Source Web Server</title>
  <style>
    :root { color-scheme: dark; font-family: system-ui, sans-serif; }
    body { margin: 0; min-height: 100vh; display: grid; place-items: center;
           background: radial-gradient(circle at top, #3b1238, #09070a 65%); color: #fff; }
    main { width: min(680px, calc(100% - 3rem)); padding: 2.5rem; border: 1px solid #fa4fc7;
           border-radius: 18px; background: #130f14e8; box-shadow: 0 20px 70px #0009; }
    h1 { color: #ff65cf; margin-top: 0; } code { color: #ff9de0; }
  </style>
</head>
<body><main><h1>Calyx Lab's Open Source Web Server is running</h1>
<p>Replace this page by editing <code>/var/calyxserver/www/index.html</code>.</p>
</main></body></html>
"""

LOG = logging.getLogger("calyxserver")


def configure_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def ensure_public_root(root: Path) -> Path:
    """Create and return the canonical public root and a starter page."""
    try:
        root.mkdir(parents=True, exist_ok=True)
        root = root.resolve(strict=True)
        index = root / "index.html"
        if not index.exists():
            index.write_text(WELCOME_PAGE, encoding="utf-8")
            try:
                index.chmod(0o644)
            except OSError:
                pass
        return root
    except PermissionError as exc:
        raise SystemExit(
            f"Permission denied while creating {root}. Run with sudo or choose "
            "another directory with --root."
        ) from exc
    except OSError as exc:
        raise SystemExit(f"Could not prepare public root {root}: {exc}") from exc


def valid_port(value: str) -> int:
    try:
        port = int(value.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be a whole number") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def prompt_for_port() -> int:
    while True:
        try:
            raw = input("Please enter a port to host the Calyx Web Server on: ")
        except (EOFError, KeyboardInterrupt):
            print("\nStartup cancelled.")
            raise SystemExit(130)
        try:
            return valid_port(raw)
        except argparse.ArgumentTypeError as exc:
            print(f"Invalid port: {exc}. Please try again.", file=sys.stderr)


class CalyxRequestHandler(SimpleHTTPRequestHandler):
    """Serve files while preventing paths and symlinks escaping public root."""

    server_version = SERVER_NAME

    def __init__(self, *args, directory: str | None = None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    def translate_path(self, path: str) -> str:
        root = Path(self.directory).resolve()
        request_path = unquote(urlsplit(path).path, errors="surrogatepass")
        request_path = posixpath.normpath(request_path)
        pieces = [part for part in request_path.split("/") if part not in ("", ".", "..")]
        candidate = root.joinpath(*pieces)
        try:
            resolved = candidate.resolve(strict=False)
            resolved.relative_to(root)
        except (OSError, ValueError):
            return str(root / ".calyx-denied")
        return str(resolved)

    def list_directory(self, path):
        """Generate an escaped directory listing without exposing local paths."""
        try:
            entries = sorted(os.listdir(path), key=str.lower)
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "No permission to list directory")
            return None
        display_path = html.escape(unquote(urlsplit(self.path).path, errors="replace"))
        rows = ["<!doctype html><html><head><meta charset='utf-8'>",
                f"<title>Directory listing for {display_path}</title></head><body>",
                f"<h1>Directory listing for {display_path}</h1><hr><ul>"]
        for name in entries:
            full = os.path.join(path, name)
            label = name + ("/" if os.path.isdir(full) else "")
            from urllib.parse import quote
            rows.append(f'<li><a href="{quote(label)}">{html.escape(label)}</a></li>')
        rows.append("</ul><hr></body></html>")
        encoded = "\n".join(rows).encode("utf-8", "surrogateescape")
        from io import BytesIO
        response = BytesIO(encoded)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return response

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()

    def log_message(self, fmt: str, *args) -> None:
        LOG.info("%s - %s", self.address_string(), fmt % args)


class CalyxHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Calyx dependency-free static web server")
    parser.add_argument("--port", type=valid_port, help="TCP port; prompts when omitted")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"bind address (default: {DEFAULT_HOST})")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help=f"public root (default: {DEFAULT_ROOT})")
    parser.add_argument("--verbose", action="store_true", help="enable debug logging")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def run_server(host: str, port: int, root: Path) -> None:
    def handler(*args, **kwargs):
        return CalyxRequestHandler(*args, directory=str(root), **kwargs)

    try:
        server = CalyxHTTPServer((host, port), handler)
    except PermissionError as exc:
        raise SystemExit(f"Permission denied binding to port {port}. Try sudo or a port above 1023.") from exc
    except OSError as exc:
        raise SystemExit(f"Could not start server on {host}:{port}: {exc}") from exc

    stop_once = threading.Event()

    def request_stop(signum=None, frame=None):
        if stop_once.is_set():
            return
        stop_once.set()
        LOG.info("Shutdown requested; stopping Calyx Web Server...")
        threading.Thread(target=server.shutdown, daemon=True).start()

    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGINT, request_stop)
        signal.signal(signal.SIGTERM, request_stop)

    shown_host = "localhost" if host in ("0.0.0.0", "::") else host
    LOG.info("Calyx Web Server %s", __version__)
    LOG.info("Serving directory: %s", root)
    LOG.info("Listening on http://%s:%d", shown_host, port)
    LOG.info("Press Ctrl+C to stop.")
    try:
        server.serve_forever(poll_interval=0.5)
    finally:
        server.server_close()
        LOG.info("Calyx Web Server stopped.")


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(args.verbose)
    root = ensure_public_root(args.root)
    port = args.port if args.port is not None else prompt_for_port()
    run_server(args.host, port, root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
