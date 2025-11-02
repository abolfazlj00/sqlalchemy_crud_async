import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models.user import (
    Address,
    User,
    UserFilterSchema,
    UserReadSchema
)
from ..bin.functions.read import read_one
from ..bin.schemas.query import FindOneRequestData, FindManyRequestData, SelectFields

@pytest.mark.asyncio
async def test_read_one_with_join(session: AsyncSession):
    """Should return a user with addresses eagerly loaded."""
    alice = User(
        name="Alice",
        age=30,
        addresses=[Address(city="Paris"), Address(city="London")],
    )
    session.add(alice)
    
    filters = UserFilterSchema(
        name="Alice"
    )
    req = FindOneRequestData(
        fields=SelectFields(
            includes=["addresses"]
        )
    )

    user = await read_one(session, User, filters, req, schema=UserReadSchema)
    assert user
    assert len(user.addresses) == 2
    cities = [a.city for a in user.addresses]
    assert "Paris" in cities
    assert "London" in cities