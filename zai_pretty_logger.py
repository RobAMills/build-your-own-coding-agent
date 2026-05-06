# zai_pretty_logger.py
from mitmproxy import http
import json
import time
from pathlib import Path

LOG_DIR = Path.cwd() / "logs"
LOG_FILE = LOG_DIR / "zai-coding-pretty.log"

UPSTREAM_HOST = "api.z.ai"
UPSTREAM_SCHEME = "https"
UPSTREAM_PREFIX = "/api/coding/paas/v4"

def setup():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def write_block(text: str) -> None:
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(text)
        f.flush()

def mask_auth(value: str | None) -> str:
    if not value:
        return ""
    if value.lower().startswith("bearer "):
        return "Bearer ***"
    return "***"

def trim(text: str | None, limit: int = 4000) -> str:
    if not text:
        return ""
    return text if len(text) <= limit else text[:limit] + "\n...<truncated>..."

def rewrite_path(path: str) -> str:
    if path.startswith("/v1/"):
        return f"{UPSTREAM_PREFIX}{path[3:]}"
    if path.startswith("/api/anthropic/v1/messages"):
        return f"{UPSTREAM_PREFIX}/messages"
    if path.startswith("/v1/messages"):
        return f"{UPSTREAM_PREFIX}/messages"
    if path.startswith("/messages"):
        return f"{UPSTREAM_PREFIX}/messages"
    return f"{UPSTREAM_PREFIX}{path}"

class PrettyLogger:
    def request(self, flow: http.HTTPFlow) -> None:
        original_path = flow.request.path
        flow.request.scheme = UPSTREAM_SCHEME
        flow.request.host = UPSTREAM_HOST
        flow.request.port = 443
        flow.request.path = rewrite_path(flow.request.path)

        content_type = flow.request.headers.get("content-type", "")
        accept = flow.request.headers.get("accept", "")
        auth = mask_auth(flow.request.headers.get("authorization"))

        body = ""
        if "application/json" in content_type.lower():
            try:
                parsed = json.loads(flow.request.get_text())
                body = json.dumps(parsed, indent=2, ensure_ascii=False)
            except Exception:
                body = flow.request.get_text()
        else:
            body = flow.request.get_text()

        block = f"""
================================================================================
REQUEST  {time.strftime("%Y-%m-%d %H:%M:%S")}
================================================================================
Method:          {flow.request.method}
Incoming Path:   {original_path}
Forwarded Path:  {flow.request.path}
URL:             {flow.request.pretty_url}
Authorization:   {auth}
Content-Type:    {content_type}
Accept:          {accept}

Headers:
"""
        for k, v in flow.request.headers.items():
            vv = mask_auth(v) if k.lower() == "authorization" else v
            if k.lower() in {"authorization", "content-type", "accept", "host"}:
                block += f"  {k}: {vv}\n"

        if body.strip():
            block += f"\nBody:\n{trim(body)}\n"

        write_block(block + "\n")

    def response(self, flow: http.HTTPFlow) -> None:
        content_type = flow.response.headers.get("content-type", "")
        body = ""

        if "application/json" in content_type.lower():
            try:
                parsed = json.loads(flow.response.get_text())
                body = json.dumps(parsed, indent=2, ensure_ascii=False)
            except Exception:
                body = flow.response.get_text()
        else:
            body = flow.response.get_text()

        block = f"""
--------------------------------------------------------------------------------
RESPONSE {time.strftime("%Y-%m-%d %H:%M:%S")}
--------------------------------------------------------------------------------
Status:          {flow.response.status_code}
Path:            {flow.request.path}
Content-Type:    {content_type}

Response Headers:
"""
        for k, v in flow.response.headers.items():
            if k.lower() in {"content-type"}:
                block += f"  {k}: {v}\n"

        if body.strip():
            block += f"\nBody:\n{trim(body)}\n"

        write_block(block + "\n")

    def error(self, flow: http.HTTPFlow) -> None:
        write_block(f"""
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
ERROR    {time.strftime("%Y-%m-%d %H:%M:%S")}
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Path:  {flow.request.path if flow.request else ""}
Error: {flow.error.msg if flow.error else "Unknown error"}

""")

addons = [PrettyLogger()]