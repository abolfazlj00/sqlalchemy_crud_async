from typing import Optional, List
from pydantic import Field
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from ...bin.schemas.models import CreateSchemaBaseModel, FilterSchemaBaseModel, ReadSchemaBaseModel, UpdateSchemaBaseModel

# -------------------------
# SQLAlchemy Base
# -------------------------
class Base(DeclarativeBase):
    pass

# -------------------------
# SQLAlchemy Models
# -------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    age: Mapped[int] = mapped_column(nullable=False)
    addresses: Mapped[List["Address"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    city: Mapped[str] = mapped_column()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user: Mapped[Optional[User]] = relationship("User", back_populates="addresses")


# -------------------------
# Pydantic Schemas
# -------------------------
class UserCreateSchema(CreateSchemaBaseModel):
    name: str
    age: int
    addresses: Optional[List["AddressCreateSchema"]] = Field(None)


class UserReadSchema(ReadSchemaBaseModel):
    id: int
    name: str
    age: int
    addresses: Optional[List["AddressReadSchema"]] = Field(None)


class UserFilterSchema(FilterSchemaBaseModel):
    id: Optional[int] = Field(None)
    name: Optional[str] = Field(None)
    age: Optional[int] = Field(None)


class UserUpdateSchema(UpdateSchemaBaseModel):
    name: Optional[str] = Field(None)
    age: Optional[int] = Field(None)


class AddressCreateSchema(CreateSchemaBaseModel):
    user_id: int
    city: str


class AddressReadSchema(ReadSchemaBaseModel):
    id: int
    user_id: int
    city: str
    # user: Optional["UserReadSchema"] = Field(None)


class AddressFilterSchema(FilterSchemaBaseModel):
    id: Optional[int] = Field(None)
    user_id: Optional[int] = Field(None)
    city: Optional[str] = Field(None)
    user: Optional[UserFilterSchema] = Field(None)


class AddressUpdateSchema(UpdateSchemaBaseModel):
    city: Optional[str] = Field(None)
    user_id: Optional[int] = Field(None)


# -------------------------
# Rebuild Pydantic models
# -------------------------
UserCreateSchema.model_rebuild()
UserReadSchema.model_rebuild()
UserFilterSchema.model_rebuild()
UserUpdateSchema.model_rebuild()
AddressCreateSchema.model_rebuild()
AddressReadSchema.model_rebuild()
AddressFilterSchema.model_rebuild()
AddressUpdateSchema.model_rebuild()
