from django.contrib import admin

from .models import Address


# Register your models here.
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    search_fields = [
        'address',
    ]
    list_display = [
        'address',
        'lat',
        'lon',
        'updated_at',
    ]
    empty_value_display = '---'
