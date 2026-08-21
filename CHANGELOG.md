# Changelog

All notable changes to Calyx Web Server are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [2.0.0] - 2026-08-21

### Added

- Introduced `config.calyx` as the primary application configuration file.
- Added support for a custom static-file working directory through `working_directory`.
- Added configurable server host, port, index files, directory listing, request timeout, maximum request-body size, connection backlog, and server header.
- Added HTTPS support using a configurable certificate and private key.
- Added the option to require a minimum of TLS 1.2 or TLS 1.3.
- Added path-prefix reverse proxying for forwarding selected requests to separately running HTTP or HTTPS applications.
- Added support for multiple reverse-proxy routes, with the most specific matching path taking priority.
- Added optional preservation of the original `Host` header.
- Added forwarding headers for communicating the original client address, protocol, and hostname to trusted backend applications.
- Added HTTPS certificate validation for secure upstream connections.
- Added per-client token-bucket rate limiting with configurable request rates, bursts, and temporary bans.
- Added IPv4 and IPv6 allow and deny rules using CIDR notation.
- Added configurable HTTP method restrictions.
- Added configuration validation through the `--check-config` command-line option.
- Added hardened response headers, including Content Security Policy, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and `Permissions-Policy`.
- Added HTTP Strict Transport Security responses when HTTPS is enabled.
- Added removal of hop-by-hop headers when forwarding reverse-proxy traffic.
- Added a redesigned, responsive default welcome page with project details and an **About Calyx Server by Calyx Labs Inc.** section.

### Changed

- Upgraded Calyx from a basic static-file server into a configurable static server and reverse-proxy gateway.
- Changed startup behavior so the application creates and reads `/var/calyxserver/config.calyx` by default.
- Expanded public-root path validation to prevent directory traversal and symbolic-link escapes.
- Improved request validation, timeout handling, upstream failure handling, and error responses.
- Improved privacy by hiding the underlying Python implementation version from the server banner.
- Expanded the README with configuration, HTTPS, reverse-proxy, testing, deployment, and hardening guidance.
- Clarified that application-level rate limiting cannot replace upstream protection against volumetric distributed denial-of-service attacks.

### Security

- Added request-rate controls and temporary client bans to reduce application-layer abuse.
- Added maximum request-body limits to reduce oversized-request attacks.
- Added socket timeouts to limit slow or stalled connections.
- Added network access rules for restricting clients by address or subnet.
- Added document-root confinement and safer path resolution.
- Added TLS minimum-version controls and secure upstream certificate validation.
- Added browser security headers and protection against server-version disclosure.

## [1.0.0] - 2026-08-20

### Added

- Released the first public version of Calyx Web Server.
- Added a dependency-free static HTTP server built entirely with the Python standard library.
- Added interactive startup through `sudo python3 calyxserver.py`.
- Added a prompt allowing the user to select the listening port.
- Added automatic creation of `/var/calyxserver/www/` as the default public document root.
- Added automatic generation of a starter `index.html` when the public root does not already contain one.
- Added static serving for HTML, CSS, JavaScript, images, downloads, and other common file types.
- Added MIME type detection using Python's standard-library facilities.
- Added concurrent request handling through a threaded HTTP server.
- Added support for index files and escaped directory listings.
- Added basic request logging and graceful shutdown using `Ctrl+C`, `SIGINT`, or `SIGTERM`.
- Added port validation for values from 1 through 65535.
- Added optional command-line settings for the host, port, public root, verbose logging, and version display.
- Added basic browser security headers.
- Added initial path traversal and symbolic-link escape protection.
- Added an MIT License, project README, `.gitignore`, and automated unit tests.

### Notes

- Version 1.0.0 focused on lightweight static website hosting and local development.
- Reverse proxying, HTTPS termination, centralized configuration, rate limiting, and advanced access controls were not included in this initial release.

[2.0.0]: https://github.com/CalyxLabsInc/CalyxWebServer/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/CalyxLabsInc/CalyxWebServer/releases/tag/v1.0.0
