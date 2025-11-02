import pytest
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models.user import (
    User,
    Address,
    UserCreateSchema,
    AddressCreateSchema,
)
from ..bin.functions.create import create_one, create_many

@pytest.mark.asyncio
async def test_create_user_with_addresses(session: AsyncSession):
    """Create a user with multiple addresses and verify via session query."""

    user_data = UserCreateSchema(
        name="Alice",
        age=30,
        addresses=[
            AddressCreateSchema(city="New York", user_id=0),
            AddressCreateSchema(city="Los Angeles", user_id=0),
        ]
    )

    # Create the user
    await create_one(session, User, user_data, commit=False)
    
    # Query the user directly from the DB
    result = (await session.execute(select(User).join(Address).where(User.name == "Alice"))).scalars().first()
    assert result
    assert result.name == "Alice"
    assert result.age == 30
    
    # Check addresses
    addresses = result.addresses
    assert addresses
    assert len(addresses) == 2
    cities = [addr.city for addr in addresses]
    assert "New York" in cities
    assert "Los Angeles" in cities


@pytest.mark.asyncio
async def test_create_multiple_users_with_addresses(session: AsyncSession):
    """Create multiple users each with addresses and verify via session query."""

    users_data = [
        UserCreateSchema(
            name="Bob",
            age=25,
            addresses=[AddressCreateSchema(city="Paris", user_id=0)]
        ),
        UserCreateSchema(
            name="Charlie",
            age=28,
            addresses=[AddressCreateSchema(city="London", user_id=0)]
        ),
    ]

    await create_many(session, User, users_data, commit=False)

    # Verify each user and their addresses
    for u_name, city in [("Bob", "Paris"), ("Charlie", "London")]:
        user = (await session.execute(select(User).join(Address).where(User.name == u_name))).scalars().first()
        assert user is not None
        assert user.name == u_name
        assert len(user.addresses) == 1
        assert user.addresses[0].city == city

@pytest.mark.asyncio
async def test_addresses_have_correct_user_id(session: AsyncSession):
    """Ensure that related addresses point to the correct user_id in DB."""

    user_data = UserCreateSchema(
        name="Diana",
        age=40,
        addresses=[
            AddressCreateSchema(city="Berlin", user_id=0),
            AddressCreateSchema(city="Madrid", user_id=0),
        ]
    )
    await create_one(session, User, user_data, commit=False)
    stmt = select(User).join(Address).where(User.name == "Diana")
    user = (await session.execute(stmt)).scalars().first()
    assert user is not None
    assert len(user.addresses) == 2

    # Verify FK linkage
    for addr in user.addresses:
        assert addr.user_id == user.id