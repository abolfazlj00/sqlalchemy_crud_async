from sqlalchemy.orm import DeclarativeBase
from typing import TypeVar
from .schemas.models import CreateSchemaBaseModel, ReadSchemaBaseModel, UpdateSchemaBaseModel, FilterSchemaBaseModel

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
    
CreateSchemaType = TypeVar("CreateSchemaType", bound=CreateSchemaBaseModel)
ReadSchemaType = TypeVar("ReadSchemaType", bound=ReadSchemaBaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=UpdateSchemaBaseModel)
FilterSchemaType = TypeVar("FilterSchemaType", bound=FilterSchemaBaseModel)