import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from .models.user import User, UserUpdateSchema, UserFilterSchema
from ..bin.functions.update import update_one, update_many


# -------------------------------------------------------------
# Utility: Insert user directly
# -------------------------------------------------------------
async def insert_user(session: AsyncSession, name: str, age: int) -> User:
    user = User(name=name, age=age)
    session.add(user)
    await session.flush()
    return user


# -------------------------------------------------------------
# Test single update
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_one_user(session: AsyncSession):
    """Basic single record update."""
    user = await insert_user(session, "Alice", 30)

    update_data = UserUpdateSchema(name="Alicia", age=31)
    filters = UserFilterSchema(id=user.id)

    updated = await update_one(session, User, filters, update_data, commit=False)

    assert updated is not None
    assert updated.id == user.id
    assert updated.name == "Alicia"
    assert updated.age == 31

    # Verify persisted within same session
    db_user = (await session.execute(select(User).where(User.id == user.id))).scalars().first()
    assert db_user.name == "Alicia"
    assert db_user.age == 31


# -------------------------------------------------------------
# Test commit persistence
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_one_commit_behavior(engine):
    """Verify commit=True makes change persistent."""

    async_session = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with async_session() as session:
        user = await insert_user(session, "Bob", 25)
        user_id = user.id
        await session.commit()

    # Update without commit (not persisted)
    async with async_session() as session:
        filters = UserFilterSchema(id=user_id)
        update_data = UserUpdateSchema(name="Bobby")
        await update_one(session, User, filters, update_data, commit=False)

    async with async_session() as session:
        db_user = (await session.execute(select(User).where(User.id == user_id))).scalars().first()
        assert db_user.name == "Bob"  # unchanged

    # Update with commit (persisted)
    async with async_session() as session:
        filters = UserFilterSchema(id=user_id)
        update_data = UserUpdateSchema(name="Robert")
        await update_one(session, User, filters, update_data, commit=True)

    async with async_session() as session:
        db_user = (await session.execute(select(User).where(User.id == user_id))).scalars().first()
        assert db_user.name == "Robert"
        await session.delete(db_user)
        await session.commit()


# -------------------------------------------------------------
# Test bulk update
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_many_users(session: AsyncSession):
    """Update multiple records at once."""
    users = [
        await insert_user(session, "U1", 20),
        await insert_user(session, "U2", 21),
        await insert_user(session, "U3", 22),
    ]

    filters = UserFilterSchema()
    update_data = UserUpdateSchema(age=99)

    updated = await update_many(session, User, filters, update_data, commit=False)

    assert len(updated) == len(users)
    for u in updated:
        assert u.age == 99

    result = await session.execute(select(User))
    for db_user in result.scalars().all():
        assert db_user.age == 99


# -------------------------------------------------------------
# Test no matches
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_many_no_matches(session: AsyncSession):
    """Return empty list if no filters match."""
    filters = UserFilterSchema(name="DoesNotExist")
    update_data = UserUpdateSchema(age=50)
    updated = await update_many(session, User, filters, update_data, commit=False)
    assert updated == []
