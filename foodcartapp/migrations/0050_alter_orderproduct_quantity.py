# Generated by Django 3.2.15 on 2022-12-22 14:37

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0049_auto_20221209_1851'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderproduct',
            name='quantity',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='количество'),
        ),
    ]
