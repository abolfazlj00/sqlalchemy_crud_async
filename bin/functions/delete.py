from sqlalchemy.ext.asyncio import AsyncSession
from ..typing import ModelType, FilterSchemaType
from ..schemas.query import FindOneRequestData, FindManyRequestData
from .read import read_one, read_many

# -------------------------------------------------------------
# Delete a single record
# -------------------------------------------------------------
async def delete_one(
    session: AsyncSession,
    model: type[ModelType],
    filters: FilterSchemaType,
    req: FindOneRequestData | None = None,
    commit: bool = False
) -> None:
    """
    Delete a single record matching filters. Does not return anything.

    Args:
        session: AsyncSession
        model: SQLAlchemy ORM model class
        filters: Pydantic filter model
        req: Optional FindOneRequestData for select fields / ordering
        commit: Whether to commit immediately
    """
    db_obj = await read_one(session, model, filters, req=req, schema=None)
    if db_obj:
        await session.delete(db_obj)
        if commit:
            await session.commit()


# -------------------------------------------------------------
# Delete multiple records
# -------------------------------------------------------------
async def delete_many(
    session: AsyncSession,
    model: type[ModelType],
    filters: FilterSchemaType,
    req: FindManyRequestData | None = None,
    commit: bool = False
) -> None:
    """
    Delete multiple records matching filters. Does not return anything.

    Args:
        session: AsyncSession
        model: SQLAlchemy ORM model class
        filters: Pydantic filter model
        req: Optional FindManyRequestData for ordering/pagination
        commit: Whether to commit immediately
    """
    objs, _, _ = await read_many(session, model, filters, req=req, schema=None)

    if objs:
        
        for obj in objs:
            await session.delete(obj)

        if commit:
            await session.commit()
