"""
This module contains wrapper that handles operations with JWT tokens
including encoding and decoding.
"""
import os
from datetime import datetime, timedelta
from typing import Any, Union

from fastapi import HTTPException
from jose import JWTError, jwt
from pydantic import ValidationError
from starlette import status

from config import settings
from models.token import TokenData, TokenType

ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 100

class JwtService:
    """
    Class that represents JWT token service used encode and decode tokens.
    """

    def __init__(self, secret: str, algorithm: str = "HS256"):
        self._secret = secret
        self._algorithm = algorithm

    def create_access_token(
            self,
            user_id: Union[str, Any],
            role: str,
    ) -> str:
        """
        Method that generates access token using predefined algorythm and key.

        :param user_id: id of user to issue token
        :type user_id: str
        :param role: user role
        :type role: str
        :return: token string
        :rtype: str
        """
        expires_delta = datetime.utcnow() + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

        to_encode = {
            "exp": expires_delta,
            "user_id": str(user_id),
            "role": role,
            "type": TokenType.access,
        }
        encoded_jwt = jwt.encode(to_encode, self._secret, self._algorithm)
        return encoded_jwt

    def create_refresh_token(
            self,
            user_id: Union[str, Any],
            role: str,
    ) -> str:
        """
        Method that generates refresh token using predefined algorythm and key.

        :param user_id: id of user to issue token
        :type user_id: str
        :param role: user role
        :type role: str
        :return: token string
        :rtype: str
        """
        expires_delta = datetime.utcnow() + timedelta(
            minutes=REFRESH_TOKEN_EXPIRE_MINUTES
        )

        to_encode = {
            "exp": expires_delta,
            "user_id": str(user_id),
            "role": role,
            "type": TokenType.refresh,
        }
        encoded_jwt = jwt.encode(to_encode, self._secret, self._algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> TokenData:
        """
        Method that decodes any token data using predefined algorythm and key.

        :param token:
        :type token:
        :return:
        :rtype:
        """
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
            token_data = TokenData(**payload)

            if datetime.fromtimestamp(token_data.exp) < datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return token_data
        except (JWTError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


jwt_service = JwtService(secret=os.environ['SECRET_KEY'])
