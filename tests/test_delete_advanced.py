import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models.user import User, UserFilterSchema, Address, AddressFilterSchema
from ..bin.functions.delete import delete_one, delete_many
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
# Test delete_one with related records (cascade)
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_user_with_addresses(session: AsyncSession):
    """Deleting a user should also remove their addresses (if cascades are configured)."""
    addr1 = Address(city="123 Main St")
    addr2 = Address(city="456 Oak St")
    user = await insert_user(session, "Alice", 30, addresses=[addr1, addr2])

    filters = UserFilterSchema(id=user.id)
    await delete_one(session, User, filters, commit=False)
    
    result_user = await session.execute(select(User).where(User.id == user.id))
    
    assert result_user.scalars().first() is None
    # Verify cascade delete occurred
    result_addr = await session.execute(select(Address))
    assert result_addr.scalars().all() == []


# -------------------------------------------------------------
# Test delete_many with ordering + pagination
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_many_with_ordering_pagination(session: AsyncSession):
    """Delete users in pages using FindManyRequestData."""
    users = [
        await insert_user(session, "U1", 20),
        await insert_user(session, "U2", 21),
        await insert_user(session, "U3", 22),
        await insert_user(session, "U4", 23),
    ]

    req = FindManyRequestData(
        pagination={"limit": 2, "page": 1},
        order_by={"column": "age", "direction": "ASC"},
    )

    filters = UserFilterSchema()
    await delete_many(session, User, filters, req=req, commit=False)

    # Only first 2 should be deleted (U1, U2)
    result = await session.execute(select(User).order_by(User.age))
    remaining = result.scalars().all()
    remaining_names = [u.name for u in remaining]
    assert "U1" not in remaining_names
    assert "U2" not in remaining_names
    assert "U3" in remaining_names
    assert "U4" in remaining_names


# -------------------------------------------------------------
# Test cascading delete on related models directly
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_many_addresses(session: AsyncSession):
    """Delete addresses linked to a user."""
    addr1 = Address(city="123 Main St")
    addr2 = Address(city="456 Oak St")
    await insert_user(session, "Bob", 40, addresses=[addr1, addr2])

    filters = AddressFilterSchema()
    await delete_many(session, Address, filters, commit=False)

    result = await session.execute(select(Address))
    assert result.scalars().all() == []
