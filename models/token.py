"""
This module contains data models related to Tokens.
"""
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from models.user import UserRole


class TokensResp(BaseModel):
    """
    Response model of token data returned in authorization APIs.
    User get both access and refresh tokens.

    :param access_token: access token
    :type  access_token: str
    :param refresh_token: refresh token
    :type  refresh_token: str
    """
    access_token: str = Field(
        ...,
        description=(
            f"Must be sent with all requests to api in the header "
            f"'Authorization: Bearer ...'"
        ),
    )
    refresh_token: str = Field(
        ...,
        description="Needed to update a pair of access & refresh tokens",
    )


class TokenType(str, Enum):
    """
    Enum class represents types of token.

    access - token type to access api methods
    refresh - token type to refresh access and refresh tokens
    """
    access = "access"
    refresh = "refresh"


class TokenData(BaseModel):
    """
    Model that represents token data used for API authorization.

    :param user_id: id of token user
    :type  user_id: UUID
    :param exp: expiration date in timestamp format
    :type  exp: int
    :param role: role of token owner, value is one of :class:`UserRole`
    :type  role: UserRole
    :param type: type of token, value is one of :class:`TokenType`
    :type type: str
    """
    user_id: UUID
    exp: int = None
    role: UserRole
    type: TokenType
