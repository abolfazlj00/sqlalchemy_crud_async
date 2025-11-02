import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from .models.user import User, UserFilterSchema
from ..bin.functions.delete import delete_one, delete_many

# -------------------------------------------------------------
# Utility: Insert user directly
# -------------------------------------------------------------
async def insert_user(session: AsyncSession, name: str, age: int) -> User:
    user = User(name=name, age=age)
    session.add(user)
    await session.flush()
    return user


# -------------------------------------------------------------
# Test delete_one basic
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_one_user(session: AsyncSession):
    """Delete a single record without commit."""
    user = await insert_user(session, "Alice", 30)
    filters = UserFilterSchema(id=user.id)

    await delete_one(session, User, filters, commit=False)

    result = await session.execute(select(User).where(User.id == user.id))
    db_user = result.scalars().first()
    assert db_user is None


# -------------------------------------------------------------
# Test delete_one with commit
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_one_commit_behavior(engine):
    """Verify commit=True makes deletion persistent."""
    async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

    # Create user and commit
    async with async_session() as session:
        user = await insert_user(session, "Bob", 25)
        user_id = user.id
        await session.commit()

    # Delete without commit (should not persist)
    async with async_session() as session:
        filters = UserFilterSchema(id=user_id)
        await delete_one(session, User, filters, commit=False)

    async with async_session() as session:
        db_user = (await session.execute(select(User).where(User.id == user_id))).scalars().first()
        assert db_user is not None  # not deleted

    # Delete with commit (persistent)
    async with async_session() as session:
        filters = UserFilterSchema(id=user_id)
        await delete_one(session, User, filters, commit=True)

    async with async_session() as session:
        db_user = (await session.execute(select(User).where(User.id == user_id))).scalars().first()
        assert db_user is None


# -------------------------------------------------------------
# Test delete_many basic
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_many_users(session: AsyncSession):
    """Delete multiple users at once."""
    users = [
        await insert_user(session, "U1", 20),
        await insert_user(session, "U2", 21),
        await insert_user(session, "U3", 22),
    ]

    filters = UserFilterSchema()
    await delete_many(session, User, filters, commit=False)

    result = await session.execute(select(User))
    assert result.scalars().all() == []


# -------------------------------------------------------------
# Test delete_many no matches
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_many_no_matches(session: AsyncSession):
    """No rows deleted if filters match none."""
    filters = UserFilterSchema(name="DoesNotExist")
    await delete_many(session, User, filters, commit=False)
    # Nothing should break or raise
