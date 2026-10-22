from decimal import Decimal
from typing import List, Optional

from ninja import Field, Schema


class RatingSchema(Schema):
    rate: float
    count: int


class RatingIn(Schema):
    rate: float = Field(..., ge=0, le=5)
    count: int = Field(0, ge=0)


class RatingPatch(Schema):
    rate: Optional[float] = Field(None, ge=0, le=5)
    count: Optional[int] = Field(None, ge=0)


class CategorySchema(Schema):
    id: int
    name: str


class CategoryIn(Schema):
    name: str = Field(..., min_length=1, max_length=255)


class CategoryPatch(Schema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class ProductSchema(Schema):
    id: int
    title: str
    price: Decimal
    description: str
    category: str = Field(..., alias="category.name")
    image: Optional[str] = None
    rating: RatingSchema

    @staticmethod
    def resolve_image(obj, context):
        if not obj.image:
            return None
        request = context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url


class ProductIn(Schema):
    title: str = Field(..., min_length=1, max_length=255)
    price: Decimal = Field(..., gt=0, max_digits=8, decimal_places=2)
    description: str
    category_id: int
    rating: RatingIn


class ProductPatch(Schema):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    price: Optional[Decimal] = Field(None, gt=0, max_digits=8, decimal_places=2)
    description: Optional[str] = None
    category_id: Optional[int] = None
    rating: Optional[RatingPatch] = None


class BuyRequestSchema(Schema):
    products: List[int]
    student: bool = False
    coupon: str = ""
    name: str = ""


class BuyResponseSchema(Schema):
    totalCost: str
    reference: str
    message: str
    error: str = ""


class ErrorSchema(Schema):
    error: str
