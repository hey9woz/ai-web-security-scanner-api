"""FastAPI application entrypoint."""

import os

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.scan import router as scan_router
from app.services.header_fetcher import UpstreamFetchError


def _parse_allowed_origins() -> list[str]:
    raw_value = os.getenv("ALLOWED_ORIGINS", "")
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


def create_app() -> FastAPI:
    """Create the FastAPI application instance."""
    app = FastAPI(title="AI Web Security Scanner API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_parse_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details = []
        for error in exc.errors():
            field = ".".join(str(part) for part in error["loc"] if part != "body")
            details.append(
                {
                    "field": field or "request",
                    "message": error["msg"],
                }
            )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "invalid_request",
                    "message": "Request validation failed.",
                    "details": details,
                }
            },
        )

    @app.exception_handler(UpstreamFetchError)
    async def handle_upstream_fetch_error(
        request: Request,
        exc: UpstreamFetchError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "error": {
                    "code": "upstream_request_failed",
                    "message": "Unable to retrieve security headers from the target URL.",
                }
            },
        )

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(scan_router)
    return app


app = create_app()
