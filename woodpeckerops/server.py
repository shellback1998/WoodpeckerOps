"""Read-only Woodpecker MCP. Keep bound to loopback until OAuth proxy is configured."""
import os
import re
from urllib.parse import quote
import httpx
from fastmcp import FastMCP

BASE = os.environ.get('WOODPECKER_URL', 'https://ci.scottgaudet.com').rstrip('/')
TOKEN = os.environ.get('WOODPECKER_TOKEN', '')
REPO = os.environ.get('WOODPECKER_REPO_ID', '4')
API_PREFIX = os.environ.get('WOODPECKER_API_PREFIX', '/api').rstrip('/')
if not TOKEN:
    raise RuntimeError('WOODPECKER_TOKEN must be configured')
if not BASE.startswith('https://'):
    raise RuntimeError('WOODPECKER_URL must use HTTPS')

mcp = FastMCP('WoodpeckerOps')

def scrub(value):
    if isinstance(value, dict):
        return {k: ('[REDACTED]' if re.search(r'token|secret|password|authorization|credential|private.?key', k, re.I) else scrub(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [scrub(v) for v in value]
    if isinstance(value, str):
        value = value.replace(TOKEN, '[REDACTED]')
        value = re.sub(r'(?i)(bearer\s+)[A-Za-z0-9._~+/-]+', r'\1[REDACTED]', value)
        return value[:30000]
    return value

async def get(path: str, params=None):
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
        response = await client.get(f'{BASE}{API_PREFIX}{path}', headers={'Authorization': f'Bearer {TOKEN}', 'Accept': 'application/json'}, params=params)
        response.raise_for_status()
        if 'json' not in response.headers.get('content-type', ''):
            return {'text': scrub(response.text[:30000])}
        return scrub(response.json())

@mcp.tool()
async def woodpecker_latest_pipeline():
    """Read the most recent pipeline for the allowlisted repository."""
    return await get(f'/repos/{quote(REPO, safe="")}/pipelines', {'page': 1, 'perPage': 1})

@mcp.tool()
async def woodpecker_list_pipelines(limit: int = 10):
    """Read recent pipeline history for the allowlisted repository."""
    return await get(f'/repos/{quote(REPO, safe="")}/pipelines', {'page': 1, 'perPage': max(1, min(limit, 30))})

@mcp.tool()
async def woodpecker_pipeline_details(number: int):
    """Read pipeline status and step details by pipeline number."""
    if number < 1: raise ValueError('Pipeline number must be positive')
    return await get(f'/repos/{quote(REPO, safe="")}/pipelines/{number}')

@mcp.tool()
async def woodpecker_step_logs(number: int, step_id: int):
    """Read a bounded amount of log output for one pipeline step."""
    if number < 1 or step_id < 1: raise ValueError('IDs must be positive')
    return await get(f'/repos/{quote(REPO, safe="")}/logs/{number}/{step_id}')


class BearerAuthMiddleware:
    """Require a valid bearer token for all incoming HTTP requests."""

    def __init__(self, app, token: str):
        import hmac

        if len(token) < 32 or token != token.strip():
            raise ValueError("Invalid WOODPECKEROPS_MCP_BEARER_TOKEN")

        self.app = app
        self.token = token.encode("utf-8")

    async def __call__(self, scope, receive, send):
        import hmac

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        supplied = None

        for key, value in scope.get("headers", []):
            if key.lower() == b"authorization":
                if supplied is not None:
                    supplied = b""
                    break
                supplied = value

        prefix = b"Bearer "

        valid = (
            supplied is not None
            and supplied.startswith(prefix)
            and hmac.compare_digest(
                supplied[len(prefix):], self.token
            )
        )

        if not valid:
            await send({
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"text/plain"),
                    (b"www-authenticate", b"Bearer"),
                    (b"cache-control", b"no-store"),
                ],
            })
            await send({
                "type": "http.response.body",
                "body": b"Unauthorized",
            })
            return

        await self.app(scope, receive, send)


def run_http():
    """Start the MCP server with mandatory HTTP authentication."""
    import uvicorn

    token = os.environ.get("WOODPECKEROPS_MCP_BEARER_TOKEN", "")

    if not token:
        raise RuntimeError(
            "WOODPECKEROPS_MCP_BEARER_TOKEN is required"
        )

    app = BearerAuthMiddleware(
        mcp.http_app(path="/mcp"),
        token,
    )

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8793,
        log_level="info",
    )


if __name__ == '__main__':
    run_http()
