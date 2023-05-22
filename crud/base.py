from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID

from fastapi import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.async_sqlalchemy import paginate
from pydantic import BaseModel
from sqlalchemy import exc
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select
from starlette import status

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
SchemaType = TypeVar("SchemaType", bound=BaseModel)
T = TypeVar("T", bound=SQLModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base Create Read Update Delete (CRUD) wrapper to handle typical
    Object-Relational Mapping operations.
    Connects Python objects and Database entries.
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialization of CRUD.

        :param model: SQLModel object model
        :type model: ModelType
        :param session: SQLModel session
        :type session: AsyncSession
        """
        self.model = model
        self.session = session

    def get_session(self) -> AsyncSession:
        """
        Helper method to get current CRUD session.

        :return: current CRUD session
        :rtype: AsyncSession
        """
        return self.session

    async def get(
        self,
        *,
        id: Union[UUID, str],
    ) -> Optional[ModelType]:
        """
        Method to get object from database by id.

        :param id: object id
        :type id: UUID | str
        :return: python object of database entry
        :rtype: ModelType
        """
        query = select(self.model).where(self.model.id == id)
        response = await self.session.execute(query)
        obj = response.scalar_one_or_none()
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Object {id} of class {self.model.__class__} not found",
            )
        return obj

    async def get_by_ids(
        self,
        *,
        list_ids: List[Union[UUID, str]],
    ) -> Optional[List[ModelType]]:
        """
        Method to get list of database objects by their respective ids.

        :param list_ids: list of ids
        :type list_ids: list[UUID | str]
        :return: list of database objects
        :rtype: list[ModelType]
        """
        response = await self.session.execute(
            select(self.model).where(self.model.id.in_(list_ids))
        )
        return response.scalars().all()

    async def get_list(
        self,
        *,
        params: Params | None = Params(),
        query: T | Select[T] | None = None,
    ) -> Page[ModelType]:
        """
        Method to get list of paginated database objects filtered by
        provided parameters.

        :param params: object filters
        :type params: Params
        :param query: filter query
        :return:
        :rtype:
        """
        if query is None:
            query = select(self.model)
        return await paginate(self.session, query, params)

    async def create(
        self,
        *,
        obj_in: Union[CreateSchemaType, ModelType],
        created_by_id: Optional[int] = None,
    ) -> ModelType:
        """
        Method to create new object in database.

        :param obj_in: object containing data to create database entry
        :type obj_in: CreateSchemaType | ModelType
        :param created_by_id: id of user who creates new object
        :type created_by_id: UUID
        :return: created object
        :rtype: ModelType
        """
        db_obj = self.model.from_orm(obj_in)  # type: ignore

        if created_by_id:
            db_obj.created_by_id = created_by_id

        try:
            self.session.add(db_obj)
            await self.session.commit()
        except exc.IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=500,
                detail="Integrity error",
            )
        await self.session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        *,
        obj_id: UUID,
        obj_new: Union[UpdateSchemaType, Dict[str, Any], ModelType],
    ) -> ModelType:
        """
        Method to update database entry.

        :param obj_id: id of modified object
        :type obj_id: UUID
        :param obj_new: object containing data to update database entry
        :type obj_new: UpdateSchemaType | dict | ModelType
        :return: updated object
        :rtype: ModelType
        """
        obj = await self.get(id=obj_id)
        values = obj_new.dict(exclude_unset=True)

        for k, v in values.items():
            setattr(obj, k, v)

        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)

        return obj

    async def delete(
        self,
        *,
        id: Union[UUID, str],
    ) -> ModelType:
        """
        Method to delete object by id.

        :param id: id of object to delete
        :type id: UUID
        :return: information about deleted object
        :rtype: ModelType
        """
        response = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        obj = response.scalar_one()
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
        return obj
