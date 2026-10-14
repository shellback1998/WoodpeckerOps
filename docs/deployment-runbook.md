# WoodpeckerOps — Deployment and Operations Runbook

Version: 1.0.0
Host: devops-manager
Repository: shellback1998/WoodpeckerOps

## 1. Purpose

WoodpeckerOps is a read-only MCP service for inspecting
Woodpecker CI pipelines associated with Scott Academy.

Supported operations:
- Retrieve latest pipeline
- List pipelines
- Retrieve pipeline details
- Retrieve pipeline step logs

## 2. Production Architecture

- Host: devops-manager
- Application directory: /opt/woodpeckerops
- Service account: piadmin
- Python environment: /opt/woodpeckerops/.venv
- Application module: woodpeckerops.server
- Local endpoint: http://127.0.0.1:8793/mcp
- Service manager: systemd
- Systemd service: woodpeckerops.service
- External hostname: woodpeckerops.scottgaudet.com
- External access: Cloudflare Tunnel and Access
- Upstream CI: https://ci.scottgaudet.com
- Authorized repository: shellback1998/scottacademy

## 3. Installation and Python Environment

Prerequisites:
- Ubuntu Linux host
- Python 3 with venv support
- Git and GitHub SSH access
- Access to the private WoodpeckerOps repository

Clone the repository:

    git clone git@github.com:shellback1998/WoodpeckerOps.git

Deploy the repository into /opt/woodpeckerops.
Ensure piadmin owns the application directory.

Create the Python environment:

    cd /opt/woodpeckerops
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt

Production Python: /opt/woodpeckerops/.venv/bin/python

## 4. Environment Configuration and Security

Production environment file:
    /etc/woodpeckerops/woodpeckerops.env

Required variables:
- WOODPECKER_URL: Woodpecker CI server URL
- WOODPECKER_API_PREFIX: API path prefix
- WOODPECKER_ALLOWED_REPO: Authorized repository
- WOODPECKER_REPO_ID: Numeric repository identifier
- WOODPECKER_TOKEN: Upstream API credential
- WOODPECKEROPS_MCP_BEARER_TOKEN: Incoming MCP credential

Use .env.example as a starting template.
Replace placeholders with securely generated credentials.
Never commit production secrets to Git.

Verified production permissions:
- /etc/woodpeckerops: 700 root:root
- woodpeckerops.env: 600 root:root

Systemd loads the environment file before starting
the application under the piadmin service account.

## 5. Systemd Service Management

Service file: /etc/systemd/system/woodpeckerops.service
Service name: woodpeckerops.service

Verified configuration:
- Type: simple
- User and Group: piadmin
- WorkingDirectory: /opt/woodpeckerops
- Restart: on-failure
- RestartSec: 5 seconds
- Startup and shutdown timeouts: 90 seconds

Install or restore the service:

    sudo install -m 644 systemd/woodpeckerops.service /etc/systemd/system/woodpeckerops.service
    sudo systemctl daemon-reload
    sudo systemctl enable --now woodpeckerops.service

Operational commands:

    systemctl status woodpeckerops.service --no-pager
    systemctl is-active woodpeckerops.service
    journalctl -u woodpeckerops.service -n 50 --no-pager
    ss -ltn "( sport = :8793 )"

Restart only after an approved change:

    sudo systemctl restart woodpeckerops.service

## 6. Cloudflare Tunnel and Access

Public MCP hostname: woodpeckerops.scottgaudet.com
Local origin: http://127.0.0.1:8793
MCP endpoint path: /mcp

Cloudflare Tunnel forwards HTTPS requests to the local service.
The origin service must remain bound to localhost.

Cloudflare Access application:
WoodpeckerOps MCP - Origin Access

Access policies include authorized email access and
service-token authentication for approved clients.

The MCP client uses these request headers:
- Authorization: Bearer <MCP_TOKEN>
- CF-Access-Client-Id: <CLIENT_ID>
- CF-Access-Client-Secret: <CLIENT_SECRET>

Never store actual header values in this repository.

## 7. MCP Tools and Verification

WoodpeckerOps exposes four read-only MCP tools:

1. woodpecker_latest_pipeline
   Retrieves the latest pipeline for the authorized repository.

2. woodpecker_list_pipelines
   Retrieves recent pipeline history.

3. woodpecker_pipeline_details
   Retrieves pipeline details and execution steps.

4. woodpecker_step_logs
   Retrieves logs for an authorized pipeline step.

Verification procedure:
- Confirm the systemd service is active.
- Confirm the service listens on 127.0.0.1:8793.
- Confirm Cloudflare Tunnel is active.
- Confirm Cloudflare Access authentication succeeds.
- Confirm the MCP client discovers all four tools.
- Retrieve the latest pipeline without modifying it.
- Verify pipeline status, branch, commit, and execution time.

All verification operations must remain read-only.

## 8. Troubleshooting

Service fails to start:
- Check systemctl status woodpeckerops.service.
- Review journalctl logs for startup errors.
- Verify the Python environment and dependencies.
- Verify required environment variables are configured.

MCP endpoint is unreachable:
- Confirm the service is active.
- Confirm port 8793 listens on 127.0.0.1.
- Confirm cloudflared.service is active.
- Verify the Cloudflare Tunnel hostname and origin.

Authentication fails:
- Verify Cloudflare Access policies.
- Verify the client service-token configuration.
- Verify the MCP bearer token configuration.
- Never display credential values in logs or tickets.

Pipeline retrieval fails:
- Verify Woodpecker CI connectivity.
- Verify the authorized repository configuration.
- Verify API endpoint compatibility.
- Check upstream API permissions and response codes.

## 9. Backup and Disaster Recovery

Source code is maintained in the private GitHub repository.
Production credentials must be backed up separately.

Recovery procedure:
1. Restore the Ubuntu host and required network access.
2. Clone shellback1998/WoodpeckerOps from GitHub.
3. Restore the application to /opt/woodpeckerops.
4. Recreate the Python virtual environment.
5. Restore credentials from an approved secure backup.
6. Restore the systemd service definition.
7. Verify Cloudflare Tunnel and Access configuration.
8. Start the WoodpeckerOps service.
9. Verify localhost connectivity and MCP authentication.
10. Test all four read-only MCP tools.

Never store credentials in Git history or documentation.
Rotate credentials if a backup or token is compromised.
