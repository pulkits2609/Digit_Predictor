"""Bounded request buffering and per-client, single-worker rate limiting."""
import time
from collections import OrderedDict, deque
from starlette.responses import JSONResponse

class SecurityMiddleware:
    def __init__(self, app, settings):
        self.app = app
        self.settings = settings
        self.clients = OrderedDict()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        if scope["method"] == "POST":
            if self.settings.rate_limit_enabled:
                now = time.monotonic()
                client = (scope.get("client") or ("unknown",))[0]
                queue = self.clients.setdefault(client, deque())
                self.clients.move_to_end(client)
                while queue and queue[0] < now - 60:
                    queue.popleft()
                if len(queue) >= self.settings.rate_limit_per_minute:
                    return await JSONResponse({"error": {"code": "rate_limited", "message": "Too many requests. Please wait a minute."}}, 429, headers={"Retry-After": "60"})(scope, receive, send)
                queue.append(now)
                if len(self.clients) > 10000:
                    self.clients.popitem(last=False)
            # Count actual received bytes; Content-Length alone is untrusted.
            limit = self.settings.upload_bytes + 65536
            headers = dict(scope.get("headers", []))
            try:
                declared = int(headers.get(b"content-length", b"0"))
            except ValueError:
                declared = limit + 1
            body = bytearray()
            if declared <= limit:
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    body.extend(message.get("body", b""))
                    if len(body) > limit or not message.get("more_body", False):
                        break
            if declared > limit or len(body) > limit:
                return await JSONResponse({"error": {"code": "upload_too_large", "message": "Upload exceeds the configured size limit."}}, 413)(scope, receive, send)
            delivered = False
            async def bounded_receive():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await receive()
            actual_receive = bounded_receive
        else:
            actual_receive = receive
        async def secured_send(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend([(b"x-content-type-options", b"nosniff"), (b"referrer-policy", b"no-referrer"), (b"cache-control", b"no-store")])
                message["headers"] = headers
            await send(message)
        await self.app(scope, actual_receive, secured_send)
