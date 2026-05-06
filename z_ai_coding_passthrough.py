# z_ai_coding_passthrough.py
from mitmproxy import http
import json
import time
from pathlib import Path

# Use script directory instead of cwd for consistent logging
SCRIPT_DIR = Path(__file__).parent.resolve()
LOG_DIR = SCRIPT_DIR / "logs"
LOG_FILE = LOG_DIR / "zai-coding-passthrough-pretty.log"

UPSTREAM_HOST = "api.z.ai"
UPSTREAM_SCHEME = "https"
UPSTREAM_PREFIX = "/api/coding/paas/v4"

STREAM_PATH_HINTS = (
    "/chat/completions",
    "/responses",
    "/messages",
    "/completions",
)

def _log(line: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def _mask_auth(value: str | None) -> str | None:
    if not value:
        return None
    if value.lower().startswith("bearer "):
        return "Bearer ***"
    return "***"

def _rewrite_path(path: str) -> str:
    if path.startswith("/v1/"):
        return f"{UPSTREAM_PREFIX}{path[3:]}"
    if path.startswith("/api/anthropic/v1/messages"):
        return f"{UPSTREAM_PREFIX}/messages"
    if path.startswith("/v1/messages"):
        return f"{UPSTREAM_PREFIX}/messages"
    if path.startswith("/messages"):
        return f"{UPSTREAM_PREFIX}/messages"
    return f"{UPSTREAM_PREFIX}{path}"

def _should_stream(path: str, accept: str, content_type: str) -> bool:
    if any(hint in path for hint in STREAM_PATH_HINTS):
        return True
    if "text/event-stream" in accept.lower():
        return True
    if "text/event-stream" in content_type.lower():
        return True
    return False

def _format_headers(headers) -> str:
    lines = []
    for key, value in headers.items:
        lines.append(f"  {key}: {value}")
    return "\n".join(lines)

def _format_json_body(text: str, indent: bool = True) -> str:
    try:
        data = json.loads(text)
        return json.dumps(data, indent=2 if indent else None, ensure_ascii=False)
    except json.JSONDecodeError:
        return text

class ZaiCodingPassthroughProxy:
    def request(self, flow: http.HTTPFlow) -> None:
        original_path = flow.request.path

        # Preserve Authorization header before modifications
        auth_before = flow.request.headers.get("Authorization") or flow.request.headers.get("authorization")

        flow.request.scheme = UPSTREAM_SCHEME
        flow.request.host = UPSTREAM_HOST
        flow.request.port = 443
        flow.request.path = _rewrite_path(flow.request.path)

        # Preserve Authorization header after modifications
        if auth_before:
            flow.request.headers["Authorization"] = auth_before

        content_type = flow.request.headers.get("content-type", "")
        accept = flow.request.headers.get("accept", "")

        # Format request body
        body_preview = ""
        if "application/json" in content_type.lower():
            body_preview = _format_json_body(flow.request.get_text())
        else:
            body_preview = flow.request.get_text()[:500]

        # Log request
        log_entry = [
            f"REQUEST  {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            f"Method:          {flow.request.method}",
            f"Incoming Path:   {original_path}",
            f"Forwarded Path:  {flow.request.path}",
            f"URL:             {flow.request.pretty_url}",
            f"Authorization:   {_mask_auth(auth_before)}",
            f"Content-Type:    {content_type}",
            f"Accept:          {accept}",
            "",
            "Request Headers:",
            _format_headers(flow.request.headers),
            "",
            "Request Body:",
            body_preview[:2000],  # Limit to 2000 chars
            "",
        ]
        _log("\n".join(log_entry))

    def responseheaders(self, flow: http.HTTPFlow) -> None:
        accept = flow.request.headers.get("Accept", "")
        content_type = flow.response.headers.get("content-type", "")

        if _should_stream(flow.request.path, accept, content_type):
            flow.response.stream = True

    def response(self, flow: http.HTTPFlow) -> None:
        content_type = flow.response.headers.get("content-type", "")

        # Format response body
        body_preview = ""
        if "application/json" in content_type.lower():
            try:
                body_preview = _format_json_body(flow.response.get_text())
            except Exception:
                body_preview = flow.response.get_text()[:500]
        else:
            body_preview = flow.response.get_text()[:500]

        # Log response
        log_entry = [
            "",
            f"RESPONSE {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "-" * 80,
            f"Status:          {flow.response.status_code}",
            f"Path:            {flow.request.path}",
            f"Content-Type:    {content_type}",
            "",
            "Response Headers:",
            _format_headers(flow.response.headers),
            "",
            "Response Body:",
            body_preview[:2000],  # Limit to 2000 chars
            "",
        ]
        _log("\n".join(log_entry))

addons = [ZaiCodingPassthroughProxy()]
