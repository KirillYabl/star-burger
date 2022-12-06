import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Product
from .models import Order
from .models import OrderProduct


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    if 'products' not in request.data:
        return Response(
            {'error': '`products` key is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    elif not isinstance(request.data['products'], list):
        return Response(
            {'error': '`products` key should be a list'},
            status=status.HTTP_400_BAD_REQUEST
        )
    elif not request.data['products']:
        return Response(
            {'error': '`products` key should contains records'},
            status=status.HTTP_400_BAD_REQUEST
        )

    order = Order.objects.create(
        address=request.data['address'],
        first_name=request.data['firstname'],
        last_name=request.data['lastname'],
        contact_phone=request.data['phonenumber'],
    )
    for product in request.data['products']:
        product_obj = get_object_or_404(Product, pk=product['product'])
        OrderProduct.objects.create(
            product=product_obj,
            quantity=product['quantity'],
            order=order
        )
    return Response({})
