from typing import (
    Callable,
    get_origin,
    get_args,
    Union,
    Optional
)
from pydantic_core import PydanticUndefined
from sqlalchemy import (
    cast,
    String,
    and_,
    or_,
    Enum,
    Select
)
from sqlalchemy.future import select
from sqlalchemy.sql.elements import ColumnElement, BinaryExpression
from sqlalchemy.orm import (
    class_mapper,
    aliased,
    load_only,
    joinedload,
)
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm.state import InstanceState
from .enum.query_operators import QueryOperator
from .schemas.query import OrderByData, PaginationData, SelectFields
from .schemas.models import ReadSchemaBaseModel
from .enum.sort_directions import SortDirection
from .typing import ModelType
# from .exceptions.invalid_filter import InvalidFilterError

def apply_order(stmt: Select, model, order: OrderByData) -> Select:
    """
    Apply ordering to a SQLAlchemy select statement (async-safe).

    Args:
        stmt: SQLAlchemy select() statement
        model: ORM model class
        order: OrderByData instance

    Returns:
        Updated select statement with ordering applied
    """
    column = getattr(model, order.column, None)
    if not column:
        raise ValueError(f"Invalid order column: {order.column}")

    if order.direction == SortDirection.ASC:
        stmt = stmt.order_by(column.asc().nullsfirst() if order.nulls_first else column.asc().nullslast())
    else:
        stmt = stmt.order_by(column.desc().nullsfirst() if order.nulls_first else column.desc().nullslast())

    return stmt

def apply_pagination(stmt: Select, pagination: PaginationData):
    return stmt.offset(pagination.offset).limit(pagination.limit)

def get_model_columns(model: ModelType):
    return [
        prop.key for prop in class_mapper(model).attrs
        if hasattr(prop, "columns") or hasattr(prop, "mapper")
    ]

def _apply_operator(column: InstrumentedAttribute, op: QueryOperator, value: any):
    mapping: dict[QueryOperator, Callable[[any], BinaryExpression]] = {
        QueryOperator.EQUAL: column.__eq__,
        QueryOperator.NOT_EQUAL: column.__ne__,
        QueryOperator.LOWER_THAN: column.__lt__,
        QueryOperator.LOWER_THAN_OR_EQUAL: column.__le__,
        QueryOperator.GREATER_THAN: column.__gt__,
        QueryOperator.GREATER_THAN_OR_EQUAL: column.__ge__,
        QueryOperator.IN: column.in_,
        QueryOperator.NOT_IN: column.not_in,
        QueryOperator.LIKE: cast(column, String).like if isinstance(column.type, Enum) else column.like,
        QueryOperator.ILIKE: cast(column, String).ilike if isinstance(column.type, Enum) else column.ilike,
        QueryOperator.STARTS_WITH: cast(column, String).startswith if isinstance(column.type, Enum) else column.startswith,
        QueryOperator.ENDS_WITH: cast(column, String).endswith if isinstance(column.type, Enum) else column.endswith
    }
    if op not in mapping:
        raise ValueError(f"Unsupported operator: {op}")
    return mapping[op](value)
 
def build_query(
    model: type[ModelType],
    filters: Optional[dict[str, any]] = None,
    aliases: Optional[dict] = None,
    select_fields: Optional[SelectFields] = None
) -> tuple[Select, ColumnElement]:
    """
    Build a SQLAlchemy select statement with nested filters and relationships (async-safe).

    Args:
        model: ORM model class
        filters: dict of filters with operators and nested relationships
        aliases: dict for already joined relationships
        select_fields: optional fields to include/exclude

    Returns:
        stmt: SQLAlchemy select statement
        filter_expr: combined filter expression
    """
    filters = filters or {}
    aliases = aliases or {}

    expressions = []

    # --- get relationships once ---
    relationships = {r.key: r for r in model.__mapper__.relationships}

    for key, value in filters.items():

        # Logical operators
        if key == QueryOperator.AND and isinstance(value, list):
            sub_exprs = [build_query(model, f, aliases)[1] for f in value]
            expressions.append(and_(*sub_exprs))
        elif key == QueryOperator.OR and isinstance(value, list):
            sub_exprs = [build_query(model, f, aliases)[1] for f in value]
            expressions.append(or_(*sub_exprs))
        # Nested relationships
        elif key in relationships:
            rel = relationships[key]
            if key not in aliases:
                aliased_rel = aliased(rel.mapper.class_)
                aliases[key] = aliased_rel
            else:
                aliased_rel = aliases[key]
            # recursive call
            _, expr = build_query(aliased_rel, value, aliases)
            expressions.append(expr)
        # Column filters
        else:
            column = getattr(model, key)
            if isinstance(value, dict):
                for op, v in value.items():
                    expressions.append(_apply_operator(column, op, v))
            else:
                expressions.append(column == value)

    # --- handle SelectFields ---
    stmt = select(model)
    all_columns = {c.key for c in model.__mapper__.columns}
    load_cols = []

    if select_fields:
        if select_fields.includes:
            if "__all__" in select_fields.includes:
                load_cols = [getattr(model, c) for c in all_columns]
                nested_paths = [p for p in select_fields.includes if p != "__all__"]
            else:
                nested_paths = select_fields.includes

            for col_path in nested_paths:
                parts = col_path.split(".")
                if len(parts) == 1:
                    if parts[0] in all_columns:
                        load_cols.append(getattr(model, parts[0]))
                    elif parts[0] in relationships:
                        stmt = stmt.options(joinedload(getattr(model, parts[0])))
                else:
                    rel_name = parts[0]
                    rel_field = parts[-1]
                    if rel_name in relationships:
                        rel_attr = getattr(model, rel_name)
                        stmt = stmt.options(
                            joinedload(rel_attr).load_only(getattr(rel_attr.mapper.class_, rel_field))
                        )

        elif select_fields.excludes:
            include_cols = [getattr(model, c) for c in all_columns if c not in select_fields.excludes]
            if include_cols:
                load_cols = include_cols

        if load_cols:
            stmt = stmt.options(load_only(*load_cols))

    filter_expr = and_(*expressions) if expressions else and_(True)
    stmt = stmt.where(filter_expr)
    return stmt, filter_expr

def lazy_schema(obj: ModelType, schema_cls: type[ReadSchemaBaseModel]) -> ReadSchemaBaseModel:
    """
    Convert a partially-loaded SQLAlchemy object to a Pydantic schema,
    including only loaded attributes.
    """
    # Get unloaded attributes
    state: InstanceState = getattr(obj, "_sa_instance_state")
    unloaded = state.unloaded  # set of unloaded attribute names
    data = {}
    for field, model_field in schema_cls.model_fields.items():
        if field in unloaded:
            continue
        value = getattr(obj, field, PydanticUndefined)
        # ---- handle type annotation ----
        annotation = model_field.annotation
        origin = get_origin(annotation)
        args = get_args(annotation)

        # Handle list of nested schemas
        if origin is list and args and issubclass(args[0], ReadSchemaBaseModel):
            if value is not None:
                value = [lazy_schema(v, args[0]) for v in value]

        # Handle Optional[List[...]]
        elif origin is Union and any(get_origin(a) is list for a in args):
            list_arg = next((a for a in args if get_origin(a) is list), None)
            if list_arg:
                inner_type = get_args(list_arg)[0]
                if issubclass(inner_type, ReadSchemaBaseModel) and value is not None:
                    value = [lazy_schema(v, inner_type) for v in value]

        # Handle single nested schema
        elif isinstance(value, DeclarativeMeta) and issubclass(annotation, ReadSchemaBaseModel):
            value = lazy_schema(value, annotation)
        data[field] = value

    return schema_cls.model_validate(data)