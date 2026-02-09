import os
import random

import anyio
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp

_TRUTHY = {"1", "true", "yes", "on"}


def fault_injection_enabled() -> bool:
    return os.getenv("NOTION_SYNTH_FAULT_INJECTION", "").strip().lower() in _TRUTHY


class FaultInjectionMiddleware(BaseHTTPMiddleware):
    """
    Opt-in failure/latency simulation for demos and tests.

    Enabled only when NOTION_SYNTH_FAULT_INJECTION is truthy. When enabled, these query
    params are recognized:
    - delay_ms: non-negative integer delay in milliseconds (applied before handling)
    - fail_rate: float in [0, 1]; when 1, always fail; otherwise probabilistic
    - fail_status: HTTP status code in [400, 599] for injected failures (default 503)
    """

    def __init__(self, app: ASGIApp, *, enabled: bool) -> None:
        super().__init__(app)
        self._enabled = enabled

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self._enabled:
            return await call_next(request)

        qp = request.query_params
        delay_ms_raw = qp.get("delay_ms")
        fail_rate_raw = qp.get("fail_rate")
        fail_status_raw = qp.get("fail_status")

        delay_ms = 0
        if delay_ms_raw is not None:
            try:
                delay_ms = int(delay_ms_raw)
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "Invalid delay_ms"})
            if delay_ms < 0 or delay_ms > 60_000:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "delay_ms must be between 0 and 60000"},
                )

        if delay_ms:
            await anyio.sleep(delay_ms / 1000.0)

        if fail_rate_raw is not None:
            try:
                fail_rate = float(fail_rate_raw)
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "Invalid fail_rate"})
            if fail_rate < 0.0 or fail_rate > 1.0:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "fail_rate must be between 0 and 1"},
                )

            status = 503
            if fail_status_raw is not None:
                try:
                    status = int(fail_status_raw)
                except ValueError:
                    return JSONResponse(status_code=400, content={"detail": "Invalid fail_status"})
                if status < 400 or status > 599:
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "fail_status must be between 400 and 599"},
                    )

            # Demo-only fault injection; randomness here is not security-sensitive.
            should_fail = fail_rate >= 1.0 or random.random() < fail_rate  # nosec B311
            if should_fail:
                headers = {"X-Notion-Synth-Fault-Injected": "true"}
                if delay_ms:
                    headers["X-Notion-Synth-Delay-Ms"] = str(delay_ms)
                return JSONResponse(
                    status_code=status,
                    headers=headers,
                    content={
                        "detail": "Injected failure",
                        "fault_injection": {
                            "delay_ms": delay_ms,
                            "fail_rate": fail_rate,
                            "status": status,
                        },
                    },
                )

        response = await call_next(request)
        if delay_ms:
            response.headers["X-Notion-Synth-Delay-Ms"] = str(delay_ms)
        return response
