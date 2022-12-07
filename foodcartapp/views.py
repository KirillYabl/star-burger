from collections import defaultdict

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from phonenumber_field.phonenumber import PhoneNumber
from phonenumbers import NumberParseException
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Product
from .models import Order
from .models import OrderProduct
from .serializers import OrderSerializer


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


def check_required_field(data, field_name, field_class):
    if field_name not in data:
        return f'`{field_name}` key is required'
    elif not isinstance(data[field_name], field_class):
        return f'`{field_name}` key should be a {field_class.__name__}'
    elif not data[field_name]:
        return f'`{field_name}` key should be not empty'
    return ''


@api_view(['POST'])
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    order = Order.objects.create(
        address=serializer.validated_data['address'],
        first_name=serializer.validated_data['first_name'],
        last_name=serializer.validated_data['last_name'],
        contact_phone=serializer.validated_data['contact_phone'],
    )
    for product in request.data['products']:
        product_obj = get_object_or_404(Product, pk=product['product'])
        OrderProduct.objects.create(
            product=product_obj,
            quantity=product['quantity'],
            order=order
        )
    return Response({})
