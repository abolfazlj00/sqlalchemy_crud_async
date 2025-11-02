import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models.user import User, UserUpdateSchema, UserFilterSchema, Address, AddressUpdateSchema
from ..bin.functions.update import update_one, update_many
from ..bin.schemas.query import FindManyRequestData

# -------------------------------------------------------------
# Utility: Insert user with optional addresses
# -------------------------------------------------------------
async def insert_user(session: AsyncSession, name: str, age: int, addresses=None) -> User:
    user = User(name=name, age=age)
    if addresses:
        user.addresses = addresses
    session.add(user)
    await session.flush()
    return user


# -------------------------------------------------------------
# Test bulk update with ordering and pagination
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_many_with_ordering(session: AsyncSession):
    """Update multiple users and check ordering doesn't break update."""
    users = [
        await insert_user(session, "U1", 20),
        await insert_user(session, "U2", 21),
        await insert_user(session, "U3", 22),
        await insert_user(session, "U4", 23)
    ]

    LIMIT = 2
    PAGE = 1

    filters = UserFilterSchema()
    update_data = UserUpdateSchema(age=99)
    req = FindManyRequestData(
        order_by={"column": "age", "direction": "DESC"},  # descending
        pagination={"limit": LIMIT, "page": PAGE}
    )

    updated = await update_many(session, User, filters, update_data, req=req, commit=False)

    # Only first page should be updated
    assert len(updated) <= LIMIT
    for u in updated:
        assert u.age == 99

    # Check remaining users
    result = await session.execute(select(User).order_by(User.id))
    all_users = result.scalars().all()
    updated_ids = [u.id for u in updated]
    for u in all_users:
        if u.id in updated_ids:
            assert u.age == 99
        else:
            assert u.age != 99  # still original


# -------------------------------------------------------------
# Test no-op update with empty UpdateSchema
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_one_no_fields(session: AsyncSession):
    """Update with empty schema should not change anything."""
    user = await insert_user(session, "Charlie", 40)
    filters = UserFilterSchema(id=user.id)
    update_data = UserUpdateSchema()  # no fields set

    updated = await update_one(session, User, filters, update_data, commit=False)

    assert updated.id == user.id
    assert updated.name == "Charlie"
    assert updated.age == 40

