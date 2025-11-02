import math
from sqlalchemy import func, select, Select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, overload, Literal
from ..typing import ModelType, FilterSchemaType, ReadSchemaType
from ..schemas.query import FindOneRequestData, FindManyRequestData
from ..utils import build_query, lazy_schema, apply_order

TotalInt = int
PagesInt = int

@overload
async def read_one(
    session: AsyncSession,
    model: type[ModelType],
    filters: FilterSchemaType,
    req: Optional[FindOneRequestData],
    schema: type[ReadSchemaType]
) -> ReadSchemaType | None: ...

@overload
async def read_one(
    session: AsyncSession,
    model: type[ModelType],
    filters: FilterSchemaType,
    req: Optional[FindOneRequestData],
    schema: Literal[None]
) -> ModelType | None: ...

async def read_one(
    session: AsyncSession,
    model: type[ModelType],
    filters: FilterSchemaType,
    req: Optional[FindOneRequestData] = None,
    schema: Optional[type[ReadSchemaType]] = None
) -> ModelType | ReadSchemaType | None:
    """
    Read a single record matching the filters, optionally converting to a Pydantic schema.

    Args:
        session: AsyncSession
        model: SQLAlchemy ORM model class
        filters: FilterSchemaType dict of filters
        req: Optional FindOneRequestData (fields to include/exclude, ordering)
        schema: Optional Pydantic schema class for serialization

    Returns:
        The matched SQLAlchemy model instance or Pydantic schema, or None if not found
    """
    if req is None:
        req = FindOneRequestData()

    # Build async-safe statement
    stmt: Select[tuple[ModelType]]
    stmt, _ = build_query(
        model=model,
        filters=filters.model_dump(exclude_unset=True),
        select_fields=req.fields
    )
    
    # Apply ordering if specified
    if req.order_by:
        stmt = apply_order(stmt, model, req.order_by)
    # Execute
    result = await session.execute(stmt)

    obj = result.scalars().first()
    
    # Convert to schema if provided
    if obj and schema:
        return lazy_schema(obj, schema)
    return obj

@overload
async def read_many(
    session: AsyncSession,
    model: type[ModelType],
    filters: FilterSchemaType,
    req: Optional[FindManyRequestData],
    schema: type[ReadSchemaType]
) -> tuple[list[ReadSchemaType], TotalInt, PagesInt]: ...

@overload
async def read_many(
    session: AsyncSession,
    model: type[ModelType],
    filters: FilterSchemaType,
    req: Optional[FindManyRequestData],
    schema: Literal[None]
) -> tuple[list[ModelType], TotalInt, PagesInt]: ...

async def read_many(
    session: AsyncSession,
    model: type[ModelType],
    filters: FilterSchemaType,
    req: Optional[FindManyRequestData] = None,
    schema: Optional[type[ReadSchemaType]] = None
) -> tuple[list[ModelType] | list[ReadSchemaType], TotalInt, PagesInt]:
    """
    Read multiple records matching the filters, with optional pagination,
    ordering, schema conversion, and return total count and total pages.

    Returns:
        Tuple[List of objects or schemas, total count, total pages]
    """
    if req is None:
        req = FindManyRequestData()

    # Build async-safe statement
    stmt, _ = build_query(
        model=model,
        filters=filters.model_dump(exclude_unset=True),
        select_fields=req.fields
    )

    # Apply ordering
    if req.order_by:
        stmt = apply_order(stmt, model, req.order_by)

    # Total count query
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())

    total_result = await session.execute(count_stmt)
    total_count = total_result.scalar_one()
    total_count = TotalInt(total_count)

    # Apply pagination
    if req.pagination:
        stmt = stmt.offset(req.pagination.offset).limit(req.pagination.limit)
        pages = PagesInt(math.ceil(total_count / req.pagination.limit))
    else:
        pages = PagesInt(1)

    # Execute main query
    result = await session.execute(stmt)
    objs = result.scalars().all()

    # Convert to schema if provided
    if schema:
        objs = [lazy_schema(obj, schema) for obj in objs]

    return objs, total_count, pages