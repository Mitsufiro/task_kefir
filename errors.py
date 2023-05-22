"""
Module that defines list of possible request errors which is sent in response.
"""
from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse


class ApiError(HTTPException):
    """
    Class of base API error.
    Used to generate status code and message for error response.
    """

    status_code = 500
    error = "internal_error"
    detail = "Unknown server error"

    def __init__(self, detail: str = None, data: dict = None) -> None:
        super().__init__(status_code=self.status_code, detail=detail or self.detail)
        self.data = data


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    """
    Method to handle API errors. Works as middleware for FastAPI application.

    :param request:
    :type request:
    :param exc:
    :type exc:
    :return:
    :rtype:
    """
    error_boby = {"error": exc.error, "detail": exc.detail}
    if exc.data:
        error_boby["data"] = exc.data  # type: ignore
    return JSONResponse(
        error_boby,
        status_code=exc.status_code,
    )


class NotFoundError(ApiError):
    status_code = 404
    error = "not_found"
    detail = "Object not found"


class BadRequestError(ApiError):
    status_code = 400
    error = "bad_request"
    detail = ""


class ForbiddenError(ApiError):
    status_code = 403
    error = "forbidden"
    detail = "Requested resource is forbidden"


class InvalidPasswordError(ApiError):
    status_code = 400
    error = "invalid_password"
    detail = "Invalid password"


class InvalidTokenError(ApiError):
    status_code = 401
    error = "invalid_token"
    detail = "Invalid auth token"
