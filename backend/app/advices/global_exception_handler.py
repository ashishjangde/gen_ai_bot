import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.advices.base_response_handler import BaseResponseHandler
from app.exceptions.exceptions import (
    InvalidCredentialsException,
    InvalidOperationException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
    UnauthorizedAccessException,
    ResourceNotVerifiedException,
    VerificationCodeExpiredException,
    ConflictException,
)

logger = logging.getLogger(__name__)


class GlobalExceptionHandler:
    """
    Global exception handler for the application.
    This class is responsible for handling exceptions and returning appropriate API error responses.
    """

    @staticmethod
    def register_exception_handlers(app: FastAPI) -> None:
        """
        Register exception handlers for the FastAPI application.
        :param app: FastAPI application instance
        """

        @app.exception_handler(ResourceNotFoundException)
        async def handle_resource_not_found(
            _request: Request, exc: ResourceNotFoundException
        ) -> JSONResponse:
            return BaseResponseHandler.error_response(
                message="Resource Not Found",
                status_code=404,
                errors={"detail": exc.message},
            )

        @app.exception_handler(InvalidCredentialsException)
        async def handle_invalid_credentials(
            _request: Request, exc: InvalidCredentialsException
        ) -> JSONResponse:
            return BaseResponseHandler.error_response(
                message="Invalid Credentials",
                status_code=401,
                errors={"detail": exc.message},
            )

        @app.exception_handler(UnauthorizedAccessException)
        async def handle_unauthorized_access(
            _request: Request, exc: UnauthorizedAccessException
        ) -> JSONResponse:
            return BaseResponseHandler.error_response(
                message="Unauthorized Access",
                status_code=403,
                errors={"detail": exc.message},
            )

        @app.exception_handler(ResourceAlreadyExistsException)
        async def handle_resource_already_exists(
            _request: Request, exc: ResourceAlreadyExistsException
        ) -> JSONResponse:
            return BaseResponseHandler.error_response(
                message="Resource Already Exists",
                status_code=409,
                errors={"detail": exc.message},
            )

        @app.exception_handler(InvalidOperationException)
        async def handle_invalid_operation(
            _request: Request, exc: InvalidOperationException
        ) -> JSONResponse:
            return BaseResponseHandler.error_response(
                message="Invalid Operation",
                status_code=400,
                errors={"detail": exc.message},
            )

        @app.exception_handler(404)
        async def not_found_handler(
            request: Request, _exc: StarletteHTTPException
        ) -> JSONResponse:
            return BaseResponseHandler.error_response(
                message="Route not found",
                status_code=404,
                errors={"path": str(request.url.path), "method": request.method},
            )

        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(
            _request: Request, exc: RequestValidationError
        ) -> JSONResponse:
            error_dict = {}
            for error in exc.errors():
                field = error["loc"][-1] if error["loc"] else "unknown"
                error_dict[str(field)] = error["msg"]

            return BaseResponseHandler.validation_error_response(error_dict)

        @app.exception_handler(ResponseValidationError)
        async def response_validation_exception_handler(
            _request: Request, exc: ResponseValidationError
        ) -> JSONResponse:
            error_dict = {}
            for error in exc.errors():
                field = error["loc"][-1] if error["loc"] else "unknown"
                error_dict[str(field)] = error["msg"]

            return BaseResponseHandler.error_response(
                message="Response Validation Error",
                status_code=500,
                errors=error_dict,
            )

        @app.exception_handler(ResourceNotVerifiedException)
        async def handle_resource_not_verified(
            _request: Request, exc: ResourceNotVerifiedException
        ) -> JSONResponse:
            return BaseResponseHandler.error_response(
                message="Resource Not Verified",
                status_code=403,
                errors={"detail": exc.message},
            )

        @app.exception_handler(VerificationCodeExpiredException)
        async def handle_verification_code_expired(
            _request: Request, exc: VerificationCodeExpiredException
        ) -> JSONResponse:
            return BaseResponseHandler.error_response(
                message="Verification Code Expired",
                status_code=400,
                errors={"detail": exc.message},
            )

        @app.exception_handler(ConflictException)
        async def handle_conflict_exception(
            _request: Request, exc: ConflictException
        ) -> JSONResponse:
            return BaseResponseHandler.error_response(
                message="Conflict detected",
                status_code=409,
                errors={"detail": exc.message},
            )

        @app.exception_handler(Exception)
        async def handle_exception(_request: Request, exc: Exception) -> JSONResponse:
            logger.error(f"Unexpected error occurred: {exc}")
            return BaseResponseHandler.error_response(
                message="Internal Server Error",
                status_code=500,
                errors={"detail": str(exc)},
            )