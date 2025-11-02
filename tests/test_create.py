import pytest
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from ..bin.functions.create import create_one, create_many
from .models.user import User, UserCreateSchema

@pytest.mark.asyncio
async def test_create_one_user(session: AsyncSession):
    data = UserCreateSchema(name="Alice", age=30)
    user = await create_one(session, User, data, commit=False)
    assert user.id is not None
    assert user.name == "Alice"
    assert user.age == 30

@pytest.mark.asyncio
async def test_create_many_users(session: AsyncSession):
    users_data = [
        UserCreateSchema(name="Bob", age=25),
        UserCreateSchema(name="Carol", age=26),
    ]
    users = await create_many(session, User, users_data, commit=False)
    assert len(users) == 2
    assert users[0].name == "Bob"
    assert users[1].name == "Carol"

@pytest.mark.asyncio
async def test_create_invalid_user(session: AsyncSession):

    with pytest.raises(Exception):
        invalid_data = UserCreateSchema(name=None, age="not-an-int")  # invalid types
        await create_one(session, User, invalid_data)

@pytest.mark.asyncio
async def test_create_one_commit_behavior(engine):

    async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

    # Create user without committing
    async with async_session() as session:
        data = UserCreateSchema(name="Dave", age=40)
        user = await create_one(session, User, data, commit=False)
        assert user.id is not None
        # Not committed

    # Query again in a new session — should NOT exist
    async with async_session() as session:
        result = await session.execute(select(User).where(User.name == "Dave"))
        assert result.scalars().first() is None

@pytest.mark.asyncio
async def test_create_one_flush_pk(session: AsyncSession):

    data = UserCreateSchema(name="Eve", age=28)
    user = await create_one(session, User, data, commit=False)
    assert user.id is not None  # PK assigned via flush

@pytest.mark.asyncio
async def test_create_many_empty(session: AsyncSession):

    users = await create_many(session, User, [], commit=False)
    assert users == []
