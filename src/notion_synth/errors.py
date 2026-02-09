from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import Request
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

_STRUCTURED_ACCEPTS = {
    "application/problem+json",
    "application/vnd.notion-synth.error+json",
}


def _wants_structured_errors(request: Request) -> bool:
    fmt = request.query_params.get("error_format", "").strip().lower()
    if fmt in {"structured", "problem"}:
        return True
    accept = request.headers.get("accept", "")
    return any(mt in accept for mt in _STRUCTURED_ACCEPTS)


def _request_id_from(request: Request) -> str:
    existing = request.headers.get("x-request-id", "").strip()
    return existing or uuid4().hex


def _set_request_id(response: Response, request_id: str) -> None:
    response.headers["X-Request-Id"] = request_id


def _error_code_for(status_code: int) -> str:
    if status_code == 400:
        return "bad_request"
    if status_code == 401:
        return "unauthorized"
    if status_code == 403:
        return "forbidden"
    if status_code == 404:
        return "not_found"
    if status_code == 409:
        return "conflict"
    if 400 <= status_code < 500:
        return "client_error"
    return "internal_error"


def install_error_handlers(app) -> None:
    """
    Install request-id middleware + opt-in structured error responses.

    Backwards compatibility:
    - Default error bodies remain FastAPI/Starlette defaults (e.g. {"detail": ...}).
    - Structured errors are only returned when requested via Accept header or query param.
    """

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = _request_id_from(request)
        request.state.request_id = request_id
        response = await call_next(request)
        _set_request_id(response, request_id)
        return response

    @app.exception_handler(StarletteHTTPException)
    async def http_exception(request: Request, exc: StarletteHTTPException):  # type: ignore[no-untyped-def]
        request_id = getattr(request.state, "request_id", None) or _request_id_from(request)

        if not _wants_structured_errors(request):
            response = await http_exception_handler(request, exc)
            _set_request_id(response, request_id)
            return response

        detail: Any = getattr(exc, "detail", None)
        message = detail if isinstance(detail, str) else "Request failed"
        details = None if isinstance(detail, str) else detail
        payload = {
            "error": {
                "code": _error_code_for(int(getattr(exc, "status_code", 500))),
                "message": message,
                "details": details,
                "request_id": request_id,
            }
        }
        response = JSONResponse(payload, status_code=int(getattr(exc, "status_code", 500)))
        _set_request_id(response, request_id)
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_exception(request: Request, exc: RequestValidationError):  # type: ignore[no-untyped-def]
        request_id = getattr(request.state, "request_id", None) or _request_id_from(request)

        if not _wants_structured_errors(request):
            response = await request_validation_exception_handler(request, exc)
            _set_request_id(response, request_id)
            return response

        payload = {
            "error": {
                "code": "validation_error",
                "message": "Validation error",
                "details": {"errors": exc.errors()},
                "request_id": request_id,
            }
        }
        response = JSONResponse(payload, status_code=422)
        _set_request_id(response, request_id)
        return response

    @app.exception_handler(Exception)
    async def unhandled_exception(request: Request, exc: Exception):  # type: ignore[no-untyped-def]
        # Never leak exception details by default.
        request_id = getattr(request.state, "request_id", None) or _request_id_from(request)

        if not _wants_structured_errors(request):
            response = JSONResponse({"detail": "Internal server error"}, status_code=500)
            _set_request_id(response, request_id)
            return response

        payload = {
            "error": {
                "code": "internal_error",
                "message": "Internal server error",
                "details": None,
                "request_id": request_id,
            }
        }
        response = JSONResponse(payload, status_code=500)
        _set_request_id(response, request_id)
        return response

