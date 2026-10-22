import uuid
from datetime import datetime
from decimal import Decimal
from typing import List

from django.db import transaction
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404
from ninja import File, NinjaAPI, Router
from ninja.files import UploadedFile

from .models import Category, Product, Rating
from .schemas import (
    BuyRequestSchema,
    BuyResponseSchema,
    CategoryIn,
    CategoryPatch,
    CategorySchema,
    ErrorSchema,
    ProductIn,
    ProductPatch,
    ProductSchema,
)

api = NinjaAPI(
    title="DEISI Shop API",
    description="API para a loja DEISI Shop, incluindo endpoints para produtos, categorias e compras.",
    version="1.0.0",
)

COUPONS = {
    "black-friday": Decimal("0.90"),
    "diw": Decimal("0.10"),
}
STUDENT_FACTOR = Decimal("0.75")
IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


@api.exception_handler(Exception)
def unhandled_error(request, exc):
    return api.create_response(request, {"error": "Erro interno do servidor"}, status=500)


def products_qs():
    return Product.objects.select_related("category", "rating")


# ---------------------------------------------------
# categories
# ---------------------------------------------------
categories = Router(tags=["Categories"])


@categories.get("", response=List[CategorySchema], summary="Lista categorias")
def list_categories(request):
    return Category.objects.all()


@categories.post(
    "", response={201: CategorySchema, 422: ErrorSchema}, summary="Cria categoria"
)
def create_category(request, data: CategoryIn):
    return 201, Category.objects.create(name=data.name)


@categories.get(
    "{category_id}",
    response={200: CategorySchema, 404: ErrorSchema},
    summary="Obtém categoria",
)
def get_category(request, category_id: int):
    return get_object_or_404(Category, id=category_id)


@categories.put(
    "{category_id}",
    response={200: CategorySchema, 404: ErrorSchema},
    summary="Substitui categoria",
)
def replace_category(request, category_id: int, data: CategoryIn):
    category = get_object_or_404(Category, id=category_id)
    category.name = data.name
    category.save()
    return category


@categories.patch(
    "{category_id}",
    response={200: CategorySchema, 404: ErrorSchema},
    summary="Atualiza categoria parcialmente",
)
def update_category(request, category_id: int, data: CategoryPatch):
    category = get_object_or_404(Category, id=category_id)
    for field, value in data.dict(exclude_unset=True).items():
        setattr(category, field, value)
    category.save()
    return category


@categories.delete(
    "{category_id}",
    response={204: None, 404: ErrorSchema},
    summary="Remove categoria (e os seus produtos)",
)
def delete_category(request, category_id: int):
    get_object_or_404(Category, id=category_id).delete()
    return 204, None


# ---------------------------------------------------
# products
# ---------------------------------------------------
products = Router(tags=["Products"])


@products.get("", response=List[ProductSchema], summary="Lista produtos")
def list_products(request, category_id: int = None):
    qs = products_qs()
    if category_id is not None:
        qs = qs.filter(category_id=category_id)
    return qs


@products.post(
    "",
    response={201: ProductSchema, 404: ErrorSchema},
    summary="Cria produto (a imagem é enviada em /products/{id}/image)",
)
def create_product(request, data: ProductIn):
    category = get_object_or_404(Category, id=data.category_id)
    with transaction.atomic():
        rating = Rating.objects.create(**data.rating.dict())
        product = Product.objects.create(
            title=data.title,
            price=data.price,
            description=data.description,
            category=category,
            rating=rating,
        )
    return 201, products_qs().get(id=product.id)


@products.get(
    "{product_id}",
    response={200: ProductSchema, 404: ErrorSchema},
    summary="Obtém produto",
)
def get_product(request, product_id: int):
    return get_object_or_404(products_qs(), id=product_id)


@products.put(
    "{product_id}",
    response={200: ProductSchema, 404: ErrorSchema},
    summary="Substitui produto",
)
def replace_product(request, product_id: int, data: ProductIn):
    return _apply_product_changes(product_id, data.dict())


@products.patch(
    "{product_id}",
    response={200: ProductSchema, 404: ErrorSchema},
    summary="Atualiza produto parcialmente",
)
def update_product(request, product_id: int, data: ProductPatch):
    return _apply_product_changes(product_id, data.dict(exclude_unset=True))


def _apply_product_changes(product_id: int, changes: dict):
    product = get_object_or_404(products_qs(), id=product_id)
    rating_changes = changes.pop("rating", None) or {}
    if "category_id" in changes:
        product.category = get_object_or_404(Category, id=changes.pop("category_id"))
    for field, value in changes.items():
        setattr(product, field, value)
    for field, value in rating_changes.items():
        if value is not None:
            setattr(product.rating, field, value)
    with transaction.atomic():
        product.rating.save()
        product.save()
    return product


@products.post(
    "{product_id}/image",
    response={200: ProductSchema, 404: ErrorSchema, 415: ErrorSchema},
    summary="Define a imagem do produto",
)
def set_product_image(request, product_id: int, image: File[UploadedFile]):
    product = get_object_or_404(products_qs(), id=product_id)
    if image.content_type not in IMAGE_TYPES:
        return 415, {"error": "Tipo de ficheiro não suportado"}
    product.image.save(image.name, image, save=True)
    return product


@products.delete(
    "{product_id}",
    response={204: None, 404: ErrorSchema},
    summary="Remove produto",
)
def delete_product(request, product_id: int):
    product = get_object_or_404(products_qs(), id=product_id)
    with transaction.atomic():
        product.rating.delete()  # remove também o produto (CASCADE)
    return 204, None


# ---------------------------------------------------
# buy
# ---------------------------------------------------
@api.post(
    "buy",
    response={200: BuyResponseSchema, 400: ErrorSchema, 404: ErrorSchema},
    tags=["Shop"],
    summary="Calcula o total da compra e devolve a referência",
)
def buy(request, data: BuyRequestSchema):
    if not data.products:
        return 400, {"error": "No products provided"}

    found = Product.objects.in_bulk(set(data.products))
    missing = sorted(set(data.products) - found.keys())
    if missing:
        return 404, {"error": f"Invalid product id: {missing[0]}"}

    total = sum((found[p_id].price for p_id in data.products), Decimal("0.00"))

    if data.student:
        total *= STUDENT_FACTOR

    coupon = data.coupon.strip().lower()
    if coupon:
        if coupon not in COUPONS:
            return 400, {"error": f"Invalid coupon: {data.coupon}"}
        total *= COUPONS[coupon]

    name = data.name.strip()
    message = (
        f"Excelente escolha, {name}! A DEISI Shop agradece a sua preferência!"
        if name
        else "Excelente escolha! Falta-nos saber o seu nome!"
    )

    return 200, {
        "totalCost": str(total.quantize(Decimal("0.01"))),
        "reference": f"{datetime.now():%d%m%y}-{uuid.uuid4().hex[:8].upper()}",
        "message": message,
        "error": "",
    }


api.add_router("categories", categories)
api.add_router("products", products)
