# zai_coding_streaming_proxy.py
from mitmproxy import http
import json
import time
from pathlib import Path

LOG_FILE = Path.home() / "zai-coding-plan.log"
UPSTREAM_HOST = "api.z.ai"
UPSTREAM_SCHEME = "https"
UPSTREAM_PREFIX = "/api/coding/paas/v4"

STREAM_PATH_HINTS = (
    "/chat/completions",
    "/responses",
    "/messages",
    "/completions",
)

def _log(obj: dict) -> None:
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

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

class ZaiCodingStreamingProxy:
    def request(self, flow: http.HTTPFlow) -> None:
        original_path = flow.request.path

        flow.request.scheme = UPSTREAM_SCHEME
        flow.request.host = UPSTREAM_HOST
        flow.request.port = 443
        flow.request.path = _rewrite_path(flow.request.path)

        content_type = flow.request.headers.get("content-type", "")
        body_preview = None

        if "application/json" in content_type.lower():
            try:
                data = json.loads(flow.request.get_text())
                body_preview = {
                    "model": data.get("model"),
                    "stream": data.get("stream"),
                    "max_tokens": data.get("max_tokens") or data.get("max_completion_tokens"),
                    "messages_count": len(data.get("messages", [])) if isinstance(data.get("messages"), list) else None,
                }
            except Exception as e:
                body_preview = {"parse_error": str(e)}

        _log({
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "request",
            "method": flow.request.method,
            "path_in": original_path,
            "path_out": flow.request.path,
            "authorization": _mask_auth(flow.request.headers.get("Authorization")),
            "content_type": content_type,
            "accept": flow.request.headers.get("Accept"),
            "body_preview": body_preview,
        })

    def responseheaders(self, flow: http.HTTPFlow) -> None:
        accept = flow.request.headers.get("Accept", "")
        content_type = flow.response.headers.get("content-type", "")

        if _should_stream(flow.request.path, accept, content_type):
            flow.response.stream = True
            _log({
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "type": "stream_enabled",
                "path": flow.request.path,
                "status_code": flow.response.status_code,
                "response_content_type": content_type,
            })

    def response(self, flow: http.HTTPFlow) -> None:
        content_type = flow.response.headers.get("content-type", "")

        if getattr(flow.response, "stream", False):
            _log({
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "type": "response_streamed",
                "status_code": flow.response.status_code,
                "path": flow.request.path,
                "content_type": content_type,
            })
            return

        preview = None
        if "application/json" in content_type.lower():
            try:
                data = json.loads(flow.response.get_text())
                preview = {
                    "id": data.get("id"),
                    "model": data.get("model"),
                    "object": data.get("object"),
                    "type": data.get("type"),
                    "error": data.get("error"),
                }
            except Exception as e:
                preview = {"parse_error": str(e)}

        _log({
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "response",
            "status_code": flow.response.status_code,
            "path": flow.request.path,
            "content_type": content_type,
            "body_preview": preview,
        })

addons = [ZaiCodingStreamingProxy()]