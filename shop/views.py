from django.shortcuts import render

from django.http import JsonResponse
from .models import Product, Category
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal
from datetime import datetime

ref_number = 0

def index_view(request):
    return render(request, 'shop/index.html')

def swagger_view(request):
    return render(request, 'shop/swagger_ui.html')

import random

@csrf_exempt
def products_view(request):

    products = Product.objects.all()

    product_data = []
    for product in products:
        product_info = {
            'id': product.id,
            'title': product.title,
            'price': float(product.price),
            'description': product.description,
            'category': product.category.name,
            'image': request.build_absolute_uri(product.image.url),  # URL absoluto da imagem
            'rating': {
                'rate': product.rating.rate,
                'count': product.rating.count,
            }
        }
        product_data.append(product_info)

    random.shuffle(product_data)

    return JsonResponse(product_data, safe=False)  # safe=False permite serializar objetos non-dict


@csrf_exempt
def product_view(request, product_id):

    product = Product.objects.get(id=product_id)

    product_info = {
        'id': product.id,
        'title': product.title,
        'price': float(product.price),
        'description': product.description,
        'category': product.category.name,
        'image': request.build_absolute_uri(product.image.url),  # URL absoluto da imagem
        'rating': {
            'rate': product.rating.rate,
            'count': product.rating.count,
        }
    }

    return JsonResponse(product_info, safe=False)  # safe=False permite serializar objetos non-dict



@csrf_exempt
def categories_view(request):

    categories = list(Category.objects.all().values_list('name', flat=True))

    return JsonResponse(categories, safe=False)

@csrf_exempt
def buy_view(request):
    global ref_number

    context = {}

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': "Invalid JSON"}, status=400)

        if not data.get('products'):
            return JsonResponse({'error': "No products provided"}, status=400)

        total_cost = 0
        for p_id in data['products']:
            try:
                product = Product.objects.get(id=p_id)
                total_cost += product.price
            except Product.DoesNotExist:
                return JsonResponse({'error': f"Invalid product id: {p_id}"}, status=400)


        if data['student'] and data['student'] == True:
            total_cost *= Decimal('0.75')

        if data['coupon'] and data['coupon'] == 'black-friday':
            total_cost *= Decimal('0.90')

        if data['coupon'] and data['coupon'] == 'diw':
            total_cost *= Decimal('0.10')

        if 'name' in data and data['name']:
            context['message'] = f"Excelente escolha, {data['name']}! A DEISI Shop agradece a sua preferência!"
        else:
            context['message'] = f'Excelente escolha! Falta-nos saber o seu nome!'

        if 'address' in data and data['address']:
            context['address'] = f"A encomenda será enviada para: {data['address']}"
        else:
            context['address'] = f'Falta-nos saber a morada!'

        context['totalCost'] = total_cost.quantize(Decimal('0.01'))  #  Arredondando para 2 casas decimais

        current_date = datetime.now()
        formatted_date = current_date.strftime("%d%m%y")  # Data no formato ddmmyy
        ref_number += 1
        reference_string = f"{formatted_date}-{ref_number:04d}"  # Concatenando com o valor
        context['reference'] = reference_string

        return JsonResponse(context, safe=False)

    return JsonResponse({'error': "Invalid HTTP method. Use HTTP POST."}, status=405)


