import os
from typing import List
from uuid import UUID

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from pydantic.main import BaseModel
from starlette import status

from crud.token import CRUDToken
from depedences.common import RequiredRoles, get_raw_token
from errors import ForbiddenError
from models.token import TokenData, TokensResp, TokenType
from models.user import DBUser, EditableUserBase, User, UserBase, UserRole
from schema import (CreateUserReq, ExpireTokenReq, LoginByEmailReq,
                    UpdateUserAdminReq, UpdateUserReq)
from utils.jwt_service import jwt_service

load_dotenv('.env')

ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
ALGORITHM = os.environ['ALGORITHM']
JWT_SECRET_KEY = os.environ['JWT_SECRET_KEY']
JWT_REFRESH_SECRET_KEY = os.environ['JWT_REFRESH_SECRET_KEY']

ROUTER = APIRouter(
    prefix="/auth",
    tags=["User"])

from crud.user import CRUDUser
from depedences.cruds import get_token_crud, get_users_crud


@ROUTER.post(
    "/create",
    status_code=status.HTTP_200_OK,
    summary="Create user",
)
async def create_user(
        new_user: CreateUserReq,
        user_crud: CRUDUser = Depends(get_users_crud)
        # token: TokenData = Depends(
        #     RequiredRoles(
        #         [
        #             UserRole.admin,
        #             UserRole.user
        #         ]
        #     )
        # )
):
    if await user_crud.check_email_user_exists(email=new_user.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="There is already a user with same email",
        )
    user = await user_crud.create_user(obj_in=new_user)
    return user


@ROUTER.post(
    "/login",
    summary="Login by credentials to get token",
    response_model=TokensResp,
)
async def login_by_email(
        req: LoginByEmailReq,
        user_crud: CRUDUser = Depends(get_users_crud), token: CRUDToken = Depends(get_token_crud)
):
    """
    API method to authorize by email and password.
    Return pairs of access and refresh tokens.

    :param req: email and password data
    :type req: LoginByEmailReq
    :param user_crud: CRUD wrapper
    :type user_crud: CRUDUser
    """

    user = await user_crud.authenticate(email=req.email, password=req.password)
    token_bl = await token.del_from_bl(user.id)
    access_token = jwt_service.create_access_token(user.id, user.role)
    refresh_token = jwt_service.create_refresh_token(user.id, user.role)
    return TokensResp(
        access_token=access_token,
        refresh_token=refresh_token,
    )


class RefreshTokenReq(BaseModel):
    """
    Model containing refresh token data.
    """
    token: str


@ROUTER.post(
    "/auth/refresh",
    status_code=status.HTTP_200_OK,
    summary="Refresh token",
    description="Returns a new pair of access and "
                "refresh tokens if refresh token is valid",
    response_model=TokensResp,
)
async def refresh(
        req: RefreshTokenReq,
):
    """
    API method to refresh access and refresh tokens by provided refresh token.

    :param req: refresh token data
    :type req: RefreshTokenReq
    """
    old_token = jwt_service.decode_token(req.token)
    if old_token.type != TokenType.refresh:
        raise ForbiddenError()
    access_token = jwt_service.create_access_token(old_token.user_id, old_token.role)
    refresh_token = jwt_service.create_refresh_token(old_token.user_id, old_token.role)
    return TokensResp(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@ROUTER.post('/logout',summary='Logout form service')
async def logout(token_data: TokenData = Depends(
    RequiredRoles([UserRole.admin, UserRole.manager, UserRole.user, ])),
        token: str = Depends(get_raw_token),
        token_crud: CRUDToken = Depends(get_token_crud)):
    """
        API method that allows to add token to black list.
    """
    logout = ExpireTokenReq(token=token, user_id=token_data.user_id)
    tokenbl = await token_crud.create_tokenbl(obj_in=logout)
    return tokenbl


@ROUTER.get(
    "/users/current",
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    response_model=UserBase,
)
async def get_current_user(
        token: TokenData = Depends(
            RequiredRoles(
                [
                    UserRole.admin,
                    UserRole.manager,
                    UserRole.user,
                ]
            )
        ),
        user_crud: CRUDUser = Depends(get_users_crud),
) -> UserBase:
    """
    API method to get current User information.

    :param token: user token
    :type token: TokenData
    :param user_crud: CRUD wrapper
    :type user_crud: CRUDUser
    """
    user = await user_crud.get(id=token.user_id)
    return user


@ROUTER.get('/get_all_users', response_model=List[EditableUserBase], summary='Get all users on pages')
async def get_all_users(
        token: TokenData = Depends(
            RequiredRoles(
                [
                    UserRole.admin,
                    UserRole.manager,
                    UserRole.user,
                ]
            )
        ),
        users_crud: CRUDUser = Depends(get_users_crud),
):
    users = await users_crud.get_all_users()
    return users


from fastapi_pagination import Page, Params


@ROUTER.get(
    "/private/users/{pk}",
    status_code=status.HTTP_200_OK,
    summary="Get user by id",
    response_model=User,
)
async def get_user_by_id(
        user_id: UUID,
        token: TokenData = Depends(
            RequiredRoles(
                [
                    UserRole.admin,
                ]
            )
        ),
        user_crud: CRUDUser = Depends(get_users_crud),
) -> UserBase:
    user = await user_crud.get(id=user_id)
    return user


@ROUTER.get(
    "/private/users",
    status_code=status.HTTP_200_OK,
    summary="Get list of users",
    response_model=Page[DBUser],
)
async def get_user_list(
        token: TokenData = Depends(
            RequiredRoles(
                [
                    UserRole.admin
                ]
            )
        ),
        params: Params = Depends(),
        user_crud: CRUDUser = Depends(get_users_crud),
) -> Page[DBUser]:
    """
    API method to get list of all Users.
    Accessible only by admins.
    """
    users = await user_crud.get_list(params=params)
    return users


@ROUTER.get('/get_user', summary='Get user by email')
async def get_user(email, user_crud: CRUDUser = Depends(get_users_crud)):
    user = await user_crud.get_by_login(email=email)
    return user.is_active


from crud.user import CRUDUser
from depedences.cruds import get_users_crud


@ROUTER.put(
    "/update/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Update user by id",
    response_model=User,
)
async def edit_user_by_id(
        user_id: UUID,
        update_user_data: UpdateUserAdminReq,
        token: TokenData = Depends(
            RequiredRoles(
                [
                    UserRole.admin,
                ]
            )
        ), user_crud: CRUDUser = Depends(get_users_crud)):
    user = await user_crud.update(obj_id=user_id, obj_new=update_user_data)
    return user


@ROUTER.put(
    "/update_current_user",
    status_code=status.HTTP_200_OK,
    summary="Update current user",
    response_model=User,
)
async def edit_current_user(
        update_user_data: UpdateUserReq,
        token: TokenData = Depends(
            RequiredRoles(
                [
                    UserRole.admin,
                    UserRole.manager,
                    UserRole.user,
                ]
            )
        ), user_crud: CRUDUser = Depends(get_users_crud)):
    user = await user_crud.update(obj_id=token.user_id, obj_new=update_user_data)
    return user


@ROUTER.delete('/private/user/delete', summary='Delete user by id')
async def delete_user(user_id: UUID, token: TokenData = Depends(RequiredRoles([UserRole.admin])),
                      user_crud: CRUDUser = Depends(get_users_crud)):
    user = await user_crud.del_user(user_id=user_id)
    return 'User deleted'
