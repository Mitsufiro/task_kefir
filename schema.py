from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from models.user import TokenBL
from utils.partial import optional


class Token(BaseModel):
    user_id: int | None = None
    access_token: str
    refresh_token: str

    class Config:
        orm_mode = True


class TokenPayload(BaseModel):
    sub: str = None
    exp: int = None


class TokenData(BaseModel):
    username: str | None = None

    class Config:
        orm_mode = True


"""
This module contains schemas for User endpoints.
"""
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from models.user import EditableUserBase, UserBase
from utils.partial import optional


class CreateUserReq(UserBase):
    """
    Schema that contains parameters to create User.

    :param password: id of user who creates this entry
    :type password: UUID
    """

    password: Optional[str]

    class Config:
        hashed_password = None


class RegisterUserReq(EditableUserBase):
    """
    Schema that contains parameters to register User.

    :param password: id of user who creates this entry
    :type password: UUID
    """

    password: Optional[str]

    class Config:
        hashed_password = None


# All these fields are optional
@optional
class UpdateUserReq(EditableUserBase):
    """
    Schema that contains parameters to update User fields accessible by user.
    """

    pass


@optional
class UpdateUserAdminReq(UserBase):
    """
    Schema that contains parameters to update any User parameters.
    """

    pass


class LoginByEmailReq(BaseModel):
    """
    Schema that contains parameters required to log in via email.

    :param email: email of registered user
    :type email: str
    :param password: user password
    :type password: str
    """

    email: EmailStr
    password: str = Field(
        ...,
        example="string",
        title="Пароль",
    )


class ExpireTokenReq(BaseModel):
    token: str
    user_id: UUID


class TokenSchema(TokenBL):
    pass


# class UserID(UserData):
#     id: int

#
# class UserInDB(UserData):
#     hashed_password: str
#
#     class Config:
#         orm_mode = True
