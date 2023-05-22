"""
This module contains common dependencies for API endpoints.
For example, user role checker dependency.
"""
from typing import List, Optional

from fastapi import Depends, Query, Security
from fastapi.security import APIKeyHeader
from jwt import PyJWTError

from crud.token import CRUDToken
from depedences.cruds import get_token_crud
from errors import ForbiddenError, InvalidTokenError
# from app.api.errors import ForbiddenError, InvalidTokenError
from models.token import TokenData, TokenType
from models.user import DBTokenbl, UserRole
from utils.jwt_service import jwt_service


def parse_access_token(
        auth_token_raw: str, raise_exception: bool = True
) -> Optional[TokenData]:
    """
    Method to parse jwt access token from string.
    """
    try:
        token = jwt_service.decode_token(auth_token_raw)
    except (ValueError, PyJWTError):
        if raise_exception:
            raise InvalidTokenError()
        else:
            return None
    if token.user_id is None:
        if raise_exception:
            raise InvalidTokenError()
        else:
            return None
    return token


async def query_access_token(
        authorization: Optional[str] = Query(None),
) -> Optional[TokenData]:
    """
    Method to get token information from query.
    """
    if authorization is None:
        return None
    return parse_access_token(authorization)


def parse_bearer_access_token(
        auth_token_raw: str, raise_exception: bool = True
) -> Optional[TokenData]:
    """
    Method to split and parse token information from header string.
    """
    _, _, token_str = auth_token_raw.partition(" ")
    return parse_access_token(token_str, raise_exception)


async def get_raw_token(
        authorization_header: Optional[str] = Security(
            APIKeyHeader(name="authorization", auto_error=False)),
        authorization: Optional[str] = Query(None)):
    if authorization_header:
        return authorization_header
    return authorization


async def optional_access_token(
        authorization: Optional[str] = Security(
            APIKeyHeader(name="authorization", auto_error=False)
        ),
) -> Optional[TokenData]:
    """
    Method to get token information from authorization header.
    """
    if authorization is None:
        return None
    return parse_bearer_access_token(authorization)


async def header_or_query_access_token(
        header_token: TokenData | None = Depends(optional_access_token),
        query_token: TokenData | None = Depends(query_access_token),
) -> TokenData:
    """
    Method used to parse token either from header of query.
    """
    token = header_token or query_token
    if token is None or token.type != TokenType.access:
        raise InvalidTokenError()
    return token


class RequiredRoles:
    """
    Dependency injection method that checks whether request's user token
    have role required to access API method.
    """

    def __init__(self, roles: List[UserRole]):
        self._roles = roles

    async def __call__(
            self, token: TokenData = Depends(header_or_query_access_token),
            user_crud: CRUDToken = Depends(get_token_crud)
    ):
        if token.role not in self._roles:
            raise ForbiddenError()
        if await user_crud.check_token_in_bl(token.user_id):
            raise InvalidTokenError
        return token
