from sqlalchemy.ext.asyncio import AsyncSession
from typing import Generic, overload, Literal
from ..typing import ModelType, CreateSchemaType, ReadSchemaType, UpdateSchemaType, FilterSchemaType
from ..functions.create import create_one, create_many
from ..functions.read import read_one, read_many, TotalInt, PagesInt
from ..functions.update import update_one, update_many
from ..functions.delete import delete_one, delete_many
from ..schemas.query import FindOneRequestData, FindManyRequestData

class CRUDBase(Generic[ModelType, CreateSchemaType, ReadSchemaType, UpdateSchemaType, FilterSchemaType]):
    def __init__(self, model_cls: type[ModelType], read_cls: type[ReadSchemaType]):
        super().__init__()
        self._model_cls = model_cls
        self._read_cls = read_cls

    async def create_one(
        self,
        session: AsyncSession,
        obj_in: CreateSchemaType,
        commit: bool = False
    ):
        return await create_one(
            session,
            self._model_cls,
            obj_in,
            commit=commit
        )

    async def create_many(
        self,
        session: AsyncSession,
        objs_in: list[CreateSchemaType],
        commit: bool = False
    ):
        return await create_many(
            session,
            self._model_cls,
            objs_in,
            commit=commit
        )
    
    @overload
    async def read_one(
        self,
        session: AsyncSession,
        filters: FilterSchemaType,
        req: FindOneRequestData | None,
        return_schema: Literal[True]
    ) -> ReadSchemaType | None: ...
        
    @overload
    async def read_one(
        self,
        session: AsyncSession,
        filters: FilterSchemaType,
        req: FindOneRequestData | None,
        return_schema: Literal[False]
    ) -> ModelType | None: ...
    
    async def read_one(
        self,
        session: AsyncSession,
        filters: FilterSchemaType,
        req: FindOneRequestData | None = None,
        return_schema: bool = False
    ):
        return await read_one(
            session,
            self._model_cls,
            filters,
            req,
            self._read_cls if return_schema else None
        )
    
    @overload
    async def read_many(
        self,
        session: AsyncSession,
        filters: FilterSchemaType,
        req: FindManyRequestData | None,
        return_schema: Literal[True]
    ) -> tuple[list[ReadSchemaType], TotalInt, PagesInt]: ...
        
    @overload
    async def read_many(
        self,
        session: AsyncSession,
        filters: FilterSchemaType,
        req: FindManyRequestData | None,
        return_schema: Literal[False]
    ) -> tuple[list[ModelType], TotalInt, PagesInt]: ...
    
    async def read_many(
        self,
        session: AsyncSession,
        filters: FilterSchemaType,
        req: FindManyRequestData | None = None,
        return_schema: bool = False
    ):
        return await read_many(
            session,
            self._model_cls,
            filters,
            req,
            self._read_cls if return_schema else None
        )

    async def update_one(
        self,
        session: AsyncSession,
        filters: FilterSchemaType,
        obj_in: UpdateSchemaType,
        req: FindOneRequestData | None = None,
        commit: bool = False,
        refresh: bool = False
    ):
        return await update_one(
            session,
            self._model_cls,
            filters,
            obj_in,
            req,
            commit=commit,
            refresh=refresh
        )
    
    async def update_many(
        self,
        session: AsyncSession,
        filters: FilterSchemaType,
        obj_in: UpdateSchemaType,
        req: FindManyRequestData | None = None,
        commit: bool = False,
        refresh: bool = False,
    ):
        return await update_many(
            session,
            self._model_cls,
            filters,
            obj_in,
            req,
            commit=commit,
            refresh=refresh
        )

    async def delete_one(
        self,
        session: AsyncSession,
        filters: FilterSchemaType,
        req: FindOneRequestData = None,
        commit: bool = False
    ):
        return await delete_one(
            session,
            self._model_cls,
            filters,
            req,
            commit=commit
        )

    async def delete_many(
        self,
        session: AsyncSession,
        filters: FilterSchemaType,
        req: FindManyRequestData = None,
        commit: bool = False
    ):
        return await delete_many(
            session,
            self._model_cls,
            filters,
            req,
            commit=commit
        )