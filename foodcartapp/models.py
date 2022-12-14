from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import F, Sum
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItemQuerySet(models.QuerySet):
    def restaurants(self):
        pass


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def with_price(self):
        return self.prefetch_related('products').annotate(price=Sum(F('products__price') * F('products__quantity')))


class Order(models.Model):
    CREATED = 'S10_CREATED'
    WAITING = 'S20_WAITING'
    PREPARING = 'S30_PREPARING'
    READY = 'S40_READY'
    DELIVERING = 'S50_DELIVERING'
    COMPLETED = 'S60_COMPLETED'
    STATUS_CHOICES = [
        (CREATED, 'Создан'),
        (WAITING, 'Ожидает'),
        (PREPARING, 'Приготовливается'),
        (READY, 'Готов'),
        (DELIVERING, 'Доставляется'),
        (COMPLETED, 'Выполнен'),
    ]

    NOT_CHOSEN = 'P10_NOT_CHOSEN'
    CASH = 'P20_CASH'
    CREDIT_CARD = 'P30_CREDIT_CARD'
    PAYMENT_CHOICES = [
        (NOT_CHOSEN, 'Не выбран'),
        (CASH, 'Налично'),
        (CREDIT_CARD, 'Картой'),
    ]

    address = models.CharField(
        'адрес',
        max_length=200,
    )
    first_name = models.CharField(
        'имя',
        max_length=100,
    )
    last_name = models.CharField(
        'фамилия',
        max_length=100,
    )
    contact_phone = PhoneNumberField(
        'контактный номер',
        region='RU',
    )
    status = models.CharField(
        'статус',
        max_length=50,
        choices=STATUS_CHOICES,
        default=CREATED,
        db_index=True,
    )
    comment = models.TextField(
        'комментарий',
        blank=True,
    )
    created_at = models.DateTimeField(
        'Дата оформления',
        default=timezone.now,
    )
    called_at = models.DateTimeField(
        'Дата звонка',
        null=True,
        blank=True,
    )
    delivered_at = models.DateTimeField(
        'Дата доставки',
        null=True,
        blank=True,
    )
    payment_type = models.CharField(
        'способ оплаты',
        max_length=50,
        choices=PAYMENT_CHOICES,
        default=NOT_CHOSEN,
    )
    responsible_restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='ответственный ресторан',
        related_name='restaurant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    objects = OrderQuerySet.as_manager()

    @property
    def client_name(self):
        return f'{self.last_name} {self.first_name}'

    def get_available_restaurants(self):
        restaurants = None
        for product in self.products.all():
            product_restaurants = {menuitem.restaurant for menuitem in product.available_restaurants() if
                                   menuitem.availability}
            if restaurants is None:
                restaurants = product_restaurants
            elif not restaurants:
                return []
            else:
                restaurants &= product_restaurants

        return list(restaurants)

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f'{self.pk}, {self.last_name} {self.first_name}, {self.address} ({self.status})'


class OrderProduct(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name='товар',
        related_name='orders',
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveSmallIntegerField(
        'количество',
        validators=[MinValueValidator(1)],
    )
    order = models.ForeignKey(
        Order,
        verbose_name='заказ',
        related_name='products',
        on_delete=models.CASCADE,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    def available_restaurants(self):
        return self.product.menu_items.all()

    class Meta:
        verbose_name = 'товар в заказе'
        verbose_name_plural = 'товары в заказе'

    def __str__(self):
        return f'Заказ {self.order.pk}, {self.product} ({self.quantity} шт.) по {self.price} руб.'
