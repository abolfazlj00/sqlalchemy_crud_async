from pydantic import (
    Field,
    model_validator,
    field_validator
)
from typing import (
    Annotated,
    List
)
from .base import ForbidExtraModel
from ..enum.sort_directions import SortDirection

class OrderByData(ForbidExtraModel):
    column: str
    direction: SortDirection = Field(
        default=SortDirection.ASC
    )
    nulls_first: bool = Field(
        default=True,
        description="Whether to put NULL values first"
    )

class SelectFields(ForbidExtraModel):
    includes: List[str] | None = Field(
        default=None,
        description="Fields to include in response (None returns all fields)"
    )
    excludes: List[str] | None = Field(
        default=None,
        description="Fields to exclude from response"
    )

    @field_validator("includes", "excludes")
    @classmethod
    def check_not_empty(cls, v):
        if v is not None:
            if len(v) == 0:
                raise ValueError("Cannot be empty!")
        return v
    
    @model_validator(mode="after")
    def check_model(self):
        if self.includes and self.excludes:
            raise ValueError("Cannot use 'includes' and 'excludes' simultaneously!")
        if not self.includes and not self.excludes:
            raise ValueError("'includes' or 'excludes' is required!")
        return self

class PaginationData(ForbidExtraModel):
    limit: Annotated[int, Field(strict=True, ge=1, le=1000)] = Field(
        default=20,
        description="Maximum number of results (1-1000); default: 20"
    )
    page: Annotated[int, Field(strict=True, ge=1)] = Field(
        default=1,
        description="Page"
    )

    @property
    def offset(self):
        return (self.page - 1) * self.limit


class FindRequestData(ForbidExtraModel):

    order_by: OrderByData | None = Field(
        default=None,
        description="Sorting criteria for the query results."
    )
    fields: SelectFields | None = Field(
        default=None,
        description="Specify columns to include or exclude in the results."
    )

class FindOneRequestData(FindRequestData): ...

class FindManyRequestData(FindRequestData):
    pagination: PaginationData | None = Field(
        default_factory=PaginationData,
        description="Pagination data"
    )
    