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
from models.user import DBTokenbl
from routers.security import get_password_hash, verify_password
from schema import ExpireTokenReq, TokenSchema


class CRUDToken(CRUDBase[DBTokenbl, TokenSchema, ExpireTokenReq]):
    async def create_tokenbl(
            self,
            *,
            obj_in: ExpireTokenReq
    ) -> DBTokenbl:
        db_obj = DBTokenbl.from_orm(obj_in)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def check_token_in_bl(
            self,
            user_id: UUID,
    ):
        """
        Method to check existence of user by email.

        :param email: user email
        :type email: str
        :return: True if user exists otherwise False
        :rtype: bool
        """
        user = await self.session.execute(select(DBTokenbl).where(DBTokenbl.user_id == user_id))

        return user.scalars().all()

    async def del_from_bl(self, user_id: UUID):
        response = await self.session.execute(
            select(DBTokenbl).where(DBTokenbl.user_id == user_id)
        )
        obj = response.scalars().all()
        if obj:
            for i in obj:
                await self.session.delete(i)
                await self.session.commit()
        return obj
