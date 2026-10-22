from ninja import Schema
from typing import List, Optional
from decimal import Decimal


# -------------------------------------------------------
# Rating Schema
# -------------------------------------------------------
class RatingSchema(Schema):
    rate: float
    count: int


# -------------------------------------------------------
# Category Schema (string apenas)
# A API devolve só o nome: "T-shirts"
# -------------------------------------------------------
class CategorySchema(Schema):
    name: str


# -------------------------------------------------------
# Product Schema
# -------------------------------------------------------
class ProductSchema(Schema):
    id: int
    title: str
    price: Decimal
    description: str
    category: str        # A tua API devolve apenas o nome
    image: str           # URL absoluta
    rating: RatingSchema


# -------------------------------------------------------
# Buy Request Schema
# -------------------------------------------------------
class BuyRequestSchema(Schema):
    products: List[int]
    student: bool
    coupon: str
    name: str


# -------------------------------------------------------
# Buy Response Schema
# -------------------------------------------------------
class BuyResponseSchema(Schema):
    totalCost: str
    reference: str
    message: str
    error: str = ""


# -------------------------------------------------------
# Error Schema
# -------------------------------------------------------
class ErrorSchema(Schema):
    error: str
