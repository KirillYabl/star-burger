from django.db import models


# Create your models here.
class Address(models.Model):
    address = models.CharField(
        'адрес',
        max_length=200,
        unique=True
    )
    lat = models.FloatField(
        'широта',
        null=True
    )
    lon = models.FloatField(
        'долгота',
        null=True
    )
    updated_at = models.DateTimeField(
        'дата обновления адреса'
    )

    def __str__(self):
        return self.address

    class Meta:
        verbose_name = 'адрес'
        verbose_name_plural = 'адреса'
