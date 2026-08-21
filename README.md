# Calyx Web Server

A dependency-free static web server and reverse proxy written in pure Python.

## Start

```bash
sudo python3 calyxserver.py
```

First run creates `/var/calyxserver/configuration/config.calyx` and `/var/calyxserver/www/index.html`. 

## Configuration

`config.calyx` controls the working directory, host and port, indexes, directory listing, HTTPS certificate and key, minimum TLS version, request timeout and body limit, connection backlog, allowed methods, IP allow/deny CIDRs, rate limit and ban interval, security headers, and reverse proxy routes.

Enable reverse proxying and add explicit path-prefix routes:

```ini
[proxy]
enabled = true
/api = http://127.0.0.1:9000
/admin = https://127.0.0.1:9443
```

Enable HTTPS:

```ini
[https]
enabled = true
certificate_file = /etc/calyxserver/tls/fullchain.pem
private_key_file = /etc/calyxserver/tls/privkey.pem
minimum_tls = 1.2
```

## Hardening Model

Calyx includes per-IP token-bucket rate limiting, temporary bans, request body and socket limits, a bounded listen backlog, IP access rules, document-root and symlink confinement, upstream allowlisting through explicit routes, TLS certificate verification for HTTPS upstreams, hop-by-hop header removal, hidden Python version, CSP, HSTS on TLS, and other security headers.

Application controls cannot stop a volumetric DDoS attack that exhausts the network link or host before Python receives traffic. Public production deployments should use upstream firewall, load balancer, CDN, or specialist DDoS filtering; run Calyx as a dedicated unprivileged user; patch Python and the OS; restrict filesystem permissions; and monitor logs. Do not enable `trust_proxy_headers` unless all direct clients are trusted proxies.

Calyx is intentionally smaller than nginx or Apache and is not yet a drop-in replacement for every production workload.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

MIT licensed.
