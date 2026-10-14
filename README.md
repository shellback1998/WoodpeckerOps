# WoodpeckerOps v1.0.0 — devops-manager

Read-only FastMCP gateway for Scott Academy Woodpecker pipelines. It binds to 127.0.0.1:8793 and MUST NOT be publicly exposed until OAuth-compatible MCP authentication and access control are installed and tested. Cloudflare Tunnel alone is not an authentication mechanism.

## Deployment

Copy this directory to `/opt/woodpeckerops` on `devops-manager`, owned by `piadmin`. Then:

```bash
cd /opt/woodpeckerops
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
sudo install -d -m 700 /etc/woodpeckerops
sudo install -m 600 .env.example /etc/woodpeckerops/woodpeckerops.env
sudoedit /etc/woodpeckerops/woodpeckerops.env
sudo chown root:root /etc/woodpeckerops/woodpeckerops.env
sudo install -m 644 systemd/woodpeckerops.service /etc/systemd/system/woodpeckerops.service
sudo systemctl daemon-reload
sudo systemctl enable --now woodpeckerops.service
sudo systemctl status woodpeckerops.service --no-pager
```

Generate a Woodpecker personal access token for a dedicated least-privilege account; set it only in the root-owned environment file. Do not paste the token into chat. The Woodpecker token itself may have write permissions, but this gateway exposes GET-only functions.

## API compatibility note

Woodpecker API endpoints vary across versions. Verify `/api/repos/{owner}/{repo}/pipelines` and `/api/repos/{owner}/{repo}/logs/{pipeline}/{step}` against your server's OpenAPI documentation before connecting. Some versions use numeric repository IDs or different log endpoints. A 404 may require adapter changes, not new permissions.

## Authentication and production readiness

Do not publish the MCP URL through a public Cloudflare hostname until an MCP-compatible OAuth layer has been configured and tested. Do not rely on a static secret embedded in a URL. Restrict inbound access, authenticate each MCP request, rate-limit, sanitize logs, and audit requests. The current redaction is defense-in-depth, not a comprehensive DLP solution. A read-only tool can still reveal sensitive logs.

The service intentionally does not offer pipeline creation, restart, cancellation, repository writes, or secret management.
