from django import forms
from django.conf import settings
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from .utils import get_distance, fetch_coordinates_handled, sort_restaurants
from foodcartapp.models import Product, Restaurant, Order


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    yandex_geo_apikey = settings.YANDEX_GEO_APIKEY

    orders = Order.objects.prefetch_related('products__product__menu_items__restaurant'). \
        with_price().exclude(status=Order.COMPLETED).order_by('status', '-created_at')

    # cache of addresses inside view to avoid make many queries for same restaurant
    view_address_cache = {}

    order_items = []
    for order in orders:
        # find lat, lon of address in order
        if order.address not in view_address_cache:
            coordinates = fetch_coordinates_handled(yandex_geo_apikey, order.address)
            view_address_cache[order.address] = coordinates

        restaurants = []
        if not order.responsible_restaurant:
            # no need to calcalute distances if has responsible restaurant
            restaurants = order.get_available_restaurants()

        # find lat, lon for every available restaurant of order
        for i, restaurant in enumerate(restaurants):
            if restaurant.address not in view_address_cache:
                coordinates = fetch_coordinates_handled(yandex_geo_apikey, restaurant.address)
                view_address_cache[restaurant.address] = coordinates

            restaurants[i] = {
                'restaurant': restaurant,
                'distance': get_distance(view_address_cache[order.address], view_address_cache[restaurant.address])
            }

        restaurant_items = sort_restaurants(restaurants)

        order_items.append(
            {
                'order': order,
                'restaurants': restaurant_items
            }
        )

    return render(request, template_name='order_items.html', context={'order_items': order_items})
