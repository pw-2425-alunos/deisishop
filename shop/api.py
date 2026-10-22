# api.py
from ninja import NinjaAPI
from .models import Product, Category
from .schemas import *
from typing import List


### copiado de views.py


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal
from datetime import datetime

ref_number = 0

###



api = NinjaAPI(
  title="DEISI Shop API",
  description="""API para a loja DEISI Shop, incluindo endpoints para produtos, categorias e compras. Aqui encontra a descrição da API e seus EndPoints""",
  version="1.0.0"
)

# ---------------------------------------------------
# categories/
# ---------------------------------------------------
@api.get("categories/",
        response=List[CategorySchema],
        tags=["Shop"],
	    description="Lista todas as categorias de produtos"
)
@api.get("categories",
        response=List[CategorySchema],
        tags=["Shop"],
	    description="Lista todas as categorias de produtos"
)
def lista_categorias(request):
    return Category.objects.all()

# ---------------------------------------------------
# products/
# ---------------------------------------------------
@api.get("products/",
        response=List[ProductSchema],
        tags=["Shop"],
	    description="Lista todos os produtos")
@api.get("products",
        response=List[ProductSchema],
        tags=["Shop"],
	    description="Lista todos os produtos")
def lista_produtos(request):
    # return Product.objects.all()
    produtos = Product.objects.select_related("category", "rating").all()

    return [
        {
            "id": p.id,
            "title": p.title,
            "price": float(p.price),
            "description": p.description,
            "category": p.category.name,
            "image": p.image.url if p.image else None,
            "rating": {
                "rate": p.rating.rate,
                "count": p.rating.count
            }
        }
        for p in produtos
    ]


# ---------------------------------------------------
# products/{id}
# ---------------------------------------------------
@api.get("products/{id}",
        response={200: ProductSchema, 404: ErrorSchema},
        tags=["Shop"],
	    description="Retorna um produto"
)
def get_produto(request, id: int):
    # return 200, get_object_or_404(Product, id=id)
    try:
        p = Product.objects.select_related("category", "rating").get(id=id)
    except Product.DoesNotExist:
        return 404, {"message": "Produto não encontrado"}

    produto = {
        "id": p.id,
        "title": p.title,
        "price": float(p.price),
        "description": p.description,
        "category": p.category.name,
        "image": request.build_absolute_uri(p.image.url) if p.image else None,
        "rating": {
            "rate": p.rating.rate,
            "count": p.rating.count,
        }
    }

    return 200, produto


# ---------------------------------------------------
# buy/
# ---------------------------------------------------
@api.post(
    "buy/",
    response={200: BuyResponseSchema, 400: ErrorSchema},
    tags=["Shop"],
    description="Recebe produtos, aplica descontos e devolve total + referência"
)
@api.post(
    "buy",
    response={200: BuyResponseSchema, 400: ErrorSchema},
    tags=["Shop"],
    description="Recebe produtos, aplica descontos e devolve total + referência"
)
def buy(request, data: BuyRequestSchema):
    global ref_number
    context: Dict = {}

    if not data.products:
        return 400, {"error": "No products provided"}

    total_cost = Decimal("0.00")
    for p_id in data.products:
        try:
            product = Product.objects.get(id=p_id)
            total_cost += product.price
        except Product.DoesNotExist:
            return 400, {"error": f"Invalid product id: {p_id}"}

    # Aplicar desconto de estudante
    if data.student:
        total_cost *= Decimal("0.75")

    # Aplicar cupões
    if data.coupon:
        if data.coupon.lower() == "black-friday":
            total_cost *= Decimal("0.90")
        elif data.coupon.lower() == "diw":
            total_cost *= Decimal("0.10")

    # Mensagem para o cliente
    if data.name:
        context["message"] = f"Excelente escolha, {data.name}! A DEISI Shop agradece a sua preferência!"
    else:
        context["message"] = "Excelente escolha! Falta-nos saber o seu nome!"

    # Total arredondado
    context["totalCost"] = str(total_cost.quantize(Decimal("0.01")))

    # Referência de pagamento
    current_date = datetime.now()
    formatted_date = current_date.strftime("%d%m%y")
    ref_number += 1
    context["reference"] = f"{formatted_date}-{ref_number:04d}"

    # Sem erro
    context["error"] = ""

    return 200, context
