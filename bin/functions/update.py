from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import class_mapper
from ..typing import ModelType, UpdateSchemaType, FilterSchemaType
from ..schemas.query import FindOneRequestData, FindManyRequestData
from .read import read_one, read_many


async def update_one(
    session: AsyncSession,
    model: type[ModelType],
    filters: FilterSchemaType,
    obj_in: UpdateSchemaType,
    req: FindOneRequestData | None = None,
    commit: bool = False,
    refresh: bool = False,
) -> ModelType | None:
    """
    Find a record using filters, then update it using a Pydantic schema.
    Performs both query + update in a single logical operation.
    """

    db_obj = await read_one(
        session=session,
        model=model,
        filters=filters,
        req=req,
        schema=None  # always return ORM
    )

    if not db_obj:
        return None

    def _apply_updates(instance: ModelType, data: dict):
        """
        Recursively apply updates from dict to SQLAlchemy instance.
        """
        mapper = class_mapper(instance.__class__)
        rel_props = {r.key: r for r in mapper.relationships}

        for key, value in data.items():
            if key in rel_props and value is not None:
                rel_class = rel_props[key].mapper.class_

                if rel_props[key].uselist:
                    setattr(
                        instance,
                        key,
                        [
                            _apply_updates(rel_class(), v.model_dump(exclude_unset=True))
                            for v in value
                        ],
                    )
                else:
                    related_obj = getattr(instance, key)
                    if related_obj is None:
                        related_obj = rel_class()
                    _apply_updates(related_obj, value.model_dump(exclude_unset=True))
                    setattr(instance, key, related_obj)
            else:
                setattr(instance, key, value)

        return instance

    update_data = obj_in.model_dump(exclude_unset=True)
    _apply_updates(db_obj, update_data)

    session.add(db_obj)
    await session.flush()

    if commit:
        await session.commit()
        if refresh:
            await session.refresh(db_obj)

    return db_obj

async def update_many(
    session: AsyncSession,
    model: type[ModelType],
    filters: FilterSchemaType,
    obj_in: UpdateSchemaType,
    req: FindManyRequestData | None = None,
    commit: bool = False,
    refresh: bool = False,
) -> list[ModelType]:
    """
    Find multiple records using filters, then update each using a Pydantic schema.
    Reuses update_one logic internally for consistent update behavior.

    Args:
        session: AsyncSession
        model: SQLAlchemy ORM model class
        filters: Pydantic filter model defining the WHERE conditions
        obj_in: Pydantic update model defining fields to modify
        req: Optional FindManyRequestData for sorting/pagination
        commit: Whether to commit after all updates
        refresh: Whether to refresh each instance after commit

    Returns:
        List of updated ORM instances
    """

    objs, _, _ = await read_many(
        session=session,
        model=model,
        filters=filters,
        req=req,
        schema=None
    )

    if not objs:
        return []

    update_data = obj_in.model_dump(exclude_unset=True)

    def _apply_updates(instance: ModelType, data: dict):
        mapper = class_mapper(instance.__class__)
        rel_props = {r.key: r for r in mapper.relationships}

        for key, value in data.items():
            if key in rel_props and value is not None:
                rel_class = rel_props[key].mapper.class_

                if rel_props[key].uselist:
                    setattr(
                        instance,
                        key,
                        [
                            _apply_updates(rel_class(), v.model_dump(exclude_unset=True))
                            for v in value
                        ],
                    )
                else:
                    related_obj = getattr(instance, key)
                    if related_obj is None:
                        related_obj = rel_class()
                    _apply_updates(related_obj, value.model_dump(exclude_unset=True))
                    setattr(instance, key, related_obj)
            else:
                setattr(instance, key, value)

        return instance

    updated: list[ModelType] = []
    for obj in objs:
        _apply_updates(obj, update_data)
        session.add(obj)
        updated.append(obj)

    await session.flush(updated)

    if commit:
        await session.commit()
        if refresh:
            for obj in updated:
                await session.refresh(obj)

    return updated
