from typing import Sequence
from sqlalchemy.orm import RelationshipProperty, class_mapper
from sqlalchemy.ext.asyncio import AsyncSession
from ..typing import ModelType, CreateSchemaType

async def create_one(
    session: AsyncSession,
    model: type[ModelType],
    obj_in: CreateSchemaType,
    commit: bool = False
) -> ModelType:
    """
    Create a new record from a Pydantic model (Pydantic v2) using async SQLAlchemy.

    Args:
        session: AsyncSession.
        model: SQLAlchemy ORM model class.
        obj_in: Pydantic model instance.
        commit: Whether to commit immediately. Default False.

    Returns:
        The created SQLAlchemy model instance.
    """

    def _convert_nested(obj, orm_class):
        """
        Recursively convert Pydantic dict to SQLAlchemy instance.
        """
        if isinstance(obj, list):
            return [_convert_nested(o, orm_class) for o in obj]
        if hasattr(obj, "model_dump"):  # Pydantic model
            data = obj.model_dump(exclude_unset=True)
        elif isinstance(obj, dict):
            data = obj
        else:
            return obj  # primitive type
        instance = orm_class()
        for key, value in data.items():
            # If the attribute is a relationship on the ORM
            if hasattr(orm_class, key):
                attr = getattr(orm_class, key)
                if isinstance(attr.property, RelationshipProperty):
                    rel_class = attr.property.mapper.class_
                    setattr(instance, key, _convert_nested(value, rel_class))
                    continue
            setattr(instance, key, value)
        return instance

    data = obj_in.model_dump(exclude_unset=True)
    # Convert top-level nested relationships
    instance = _convert_nested(data, model)
    session.add(instance)
    await session.flush([instance])  # flush to assign PK / DB defaults
    if commit:
        await session.commit()
    return instance

async def create_many(
    session: AsyncSession,
    model: type[ModelType],
    objs_in: Sequence[CreateSchemaType],
    commit: bool = False
) -> list[ModelType]:
    """
    Create multiple records from a sequence of Pydantic models, supporting nested relationships.
    """
    def _convert_nested(obj, orm_class):
        if hasattr(obj, "model_dump"):
            data = obj.model_dump(exclude_unset=True)
        elif isinstance(obj, dict):
            data = obj
        else:
            return obj

        mapper = class_mapper(orm_class)
        rel_props = {r.key: r for r in mapper.relationships}

        # Create instance with non-relationship fields
        instance = orm_class(**{k: v for k, v in data.items() if k not in rel_props})

        # Assign relationships recursively
        for key, value in data.items():
            if key in rel_props and value is not None:
                rel_class = rel_props[key].mapper.class_
                if rel_props[key].uselist:
                    setattr(instance, key, [_convert_nested(v, rel_class) for v in value])
                else:
                    setattr(instance, key, _convert_nested(value, rel_class))

        return instance

    instances = [_convert_nested(obj, model) for obj in objs_in]

    session.add_all(instances)
    await session.flush(instances)  # flush to assign PKs / DB defaults
    if commit:
        await session.commit()
    return instances