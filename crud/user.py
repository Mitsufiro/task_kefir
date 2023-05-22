"""
Module that contains User CRUD subclass. Contains custom logic to handle
user retrieval, creation and authentication.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy import select
from starlette import status

from crud.base import CRUDBase, ModelType
from models.user import DBUser
from routers.security import get_password_hash, verify_password
from schema import CreateUserReq, UpdateUserReq


class CRUDUser(CRUDBase[DBUser, CreateUserReq, UpdateUserReq]):
    """
    Wrapper to handle User CRUD operations.
    """

    async def get_by_login(
            self,
            *,
            email: str,
    ) -> DBUser | None:
        """
        Method to get user by email.

        :param email: user email
        :type email: str
        :return: user object
        :rtype: DBUser
        """
        users = await self.session.execute(select(DBUser).where(DBUser.email == email))
        return users.scalar_one_or_none()

    async def get_all_users(self) -> Optional[List[ModelType]]:
        users = await self.session.execute(select(DBUser))
        return users.scalars().all()

    async def check_email_user_exists(
            self,
            email: str,
    ) -> bool:
        """
        Method to check existence of user by email.

        :param email: user email
        :type email: str
        :return: True if user exists otherwise False
        :rtype: bool
        """
        user = await self.get_by_login(email=email)
        if user:
            return True
        else:
            return False

    async def create_user(
            self,
            *,
            obj_in: CreateUserReq
            # role: UserRole | None = UserRole.user,
    ) -> DBUser:
        """
        Method to create new user generating additional data required in database.

        :param obj_in: request data object
        :type obj_in: CreateUserReq | RegisterUserReq
        :return: new user object
        :rtype: DBUser
        """
        db_obj = DBUser.from_orm(obj_in)
        # db_obj.role = role
        db_obj.hashed_password = get_password_hash(obj_in.password)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def authenticate(
            self,
            *,
            email: str,
            password: str,
    ) -> DBUser | None:
        """
        Method to authenticate user by comparing provided values and
        database entry.

        :param email: user email
        :type email: str
        :param password: user password
        :type password: str
        :return: user object
        :rtype: DBUser | None
        """
        user = await self.get_by_login(email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Could not find credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    async def del_user(self, user_id: UUID):
        response = await self.session.execute(
            select(DBUser).where(DBUser.id == user_id)
        )
        obj = response.scalar_one_or_none()
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
        return obj
