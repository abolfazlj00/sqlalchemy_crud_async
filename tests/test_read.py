import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from .models.user import User, UserCreateSchema, UserReadSchema, UserFilterSchema
from ..bin.functions.create import create_many
from ..bin.functions.read import read_one, read_many
from ..bin.schemas.query import FindOneRequestData, FindManyRequestData, PaginationData, OrderByData, SelectFields
from ..bin.enum.sort_directions import SortDirection

@pytest.mark.asyncio
async def test_read_one_basic(session: AsyncSession):
    """Should return a single user that matches filters."""
    session.add_all(
        [
            User(name="Alice", age=30),
            User(name="Bob", age=25)
        ]
    )
    filters = UserFilterSchema(
        name="Alice"
    )
    req = None

    result = await read_one(session, User, filters, req, schema=None)
    assert result is not None
    assert result.name == "Alice"


@pytest.mark.asyncio
async def test_read_one_with_schema(session: AsyncSession):
    """Should convert result to Pydantic schema."""
    session.add_all(
        [
            User(name="Charlie", age=30),
            User(name="Alice", age=30),
            User(name="Charlie", age=25),
        ]
    )
    filters = UserFilterSchema(
        name="Charlie"
    )
    req = FindOneRequestData(
        order_by=OrderByData(column="age", direction=SortDirection.ASC),
    )

    result = await read_one(session, User, filters, req=req, schema=UserReadSchema)
    assert result is not None
    assert isinstance(result, UserReadSchema)
    assert "addresses" not in result.model_fields_set
    assert result.name == "Charlie"
    assert result.age == 25

@pytest.mark.asyncio
async def test_read_many_basic(session: AsyncSession):
    """Should return all users and total count."""
    session.add_all(
        [
            User(name="Dan", age=20),
            User(name="Eve", age=21),
            User(name="Frank", age=22),
        ]
    )
    filters = UserFilterSchema()

    result, total, pages = await read_many(session, User, filters, req=None, schema=None)

    assert isinstance(result, list)
    assert total >= 3
    assert pages >= 1
    assert all(isinstance(u, User) for u in result)

@pytest.mark.asyncio
async def test_read_many_with_ordering(session: AsyncSession):
    """Should respect order_by in request."""

    # Seed users with different ages
    session.add_all(
        [
            User(name="Alice", age=30),
            User(name="Bob", age=25),
            User(name="Charlie", age=35),
        ]
    )

    filters = UserFilterSchema()
    req = FindManyRequestData(order_by=OrderByData(column="age", direction=SortDirection.DESC))

    result, total, pages = await read_many(session, User, filters, req=req, schema=None)

    # There should be at least 3 users
    assert total == 3
    assert pages == 1
    assert len(result) >= 3

    # Verify descending order
    ages = [u.age for u in result]
    assert ages == sorted(ages, reverse=True)

@pytest.mark.asyncio
async def test_read_many_with_pagination(session: AsyncSession):
    """Should return correct number of pages and limited results."""
    users = [
        User(name="Alice", age=30),
        User(name="Bob", age=25),
        User(name="Charlie", age=35),
    ]
    session.add_all(users)

    LIMIT = 2
    PAGE = 1
    filters = UserFilterSchema()
    req = FindManyRequestData(
        pagination=PaginationData(limit=LIMIT, page=PAGE)
    )

    result, total, pages = await read_many(session, User, filters, req, schema=None)

    assert len(result) <= LIMIT
    assert total == len(users)
    assert pages == (total + 1) // 2 or pages == (total // 2)
