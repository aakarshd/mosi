from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class NotFoundError(Exception):
    def __init__(self, resource: str, identifier: str | int):
        self.resource = resource
        self.identifier = identifier


class ValidationError(Exception):
    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details


class AuthorizationError(Exception):
    def __init__(self, message: str = "Not authorized"):
        self.message = message


def _error_response(status_code: int, code: str, message: str, details: dict | None = None) -> JSONResponse:
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        return _error_response(404, "NOT_FOUND", f"{exc.resource} '{exc.identifier}' not found")

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError):
        return _error_response(400, "VALIDATION_ERROR", exc.message, exc.details)

    @app.exception_handler(AuthorizationError)
    async def authorization_handler(request: Request, exc: AuthorizationError):
        return _error_response(403, "FORBIDDEN", exc.message)

    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc: Exception):
        return _error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
