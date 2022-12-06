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
    errors = defaultdict(set)
    fields = {
        'address': str,
        'firstname': str,
        'lastname': str,
        'phonenumber': str,
        'products': list
    }
    for field_name, field_class in fields.items():
        error = check_required_field(request.data, field_name, field_class)
        if error:
            errors[field_name].add(error)

    phonenumber_exist_and_str = 'phonenumber' in request.data and isinstance(request.data['phonenumber'], str)
    if phonenumber_exist_and_str:
        try:
            phonenumber = PhoneNumber.from_string(request.data['phonenumber'], 'RU')
            if not phonenumber.is_valid():
                errors['phonenumber'].add('Wrong phonenumber')
        except NumberParseException:
            errors['phonenumber'].add('Invalid phonenumber')

    product_ids = Product.objects.all().values_list('id', flat=True)
    for product in request.data['products']:
        error = check_required_field(product, 'product', int)
        if error:
            errors['products'].add(error)
        else:
            if product['product'] not in product_ids:
                errors['products'].add(f"product '{product['product']}' does not exist")
        error = check_required_field(product, 'quantity', int)
        if error:
            errors['products'].add(error)
        else:
            if product['quantity'] < 1:
                errors['products'].add('quantity should be greater then 0')

    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

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
