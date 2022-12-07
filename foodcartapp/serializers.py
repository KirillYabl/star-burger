from collections import OrderedDict

from django.utils.functional import cached_property
from rest_framework.fields import SkipField
from rest_framework.relations import PKOnlyObject
from rest_framework.serializers import ModelSerializer
from rest_framework.utils.serializer_helpers import BindingDict

from .models import Order
from .models import OrderProduct


class MapFieldsModelSerializer(ModelSerializer):
    """
    A model serializer with custom field names.

    It useful when frontend keys different from field names of models.
    It needs :field_name_map: dict, which keys are source field names and values is custom names.

    Also, to get validated_data with source field names, you should use validated_data_source
    """
    field_name_map = {}

    @cached_property
    def fields(self):
        """
        Replace source names to custom.

        Method can not use super method, super will raise with KeyError.
        """
        fields = BindingDict(self)
        for key, value in self.get_fields().items():
            fields[self.field_name_map[key]] = value
        return fields

    @property
    def validated_data_source(self):
        if not hasattr(self, '_validated_data'):
            msg = 'You must call `.is_valid()` before accessing `.validated_data`.'
            raise AssertionError(msg)
        if not hasattr(self, '_validated_data_source'):
            reverse_field_name_map = {value: key for key, value in self.field_name_map.items()}
            new_validated_data = {}
            for key, value in self._validated_data.items():
                new_validated_data[reverse_field_name_map[key]] = value
            self._validated_data_source = new_validated_data
        return self._validated_data_source


class OrderProductSerializer(ModelSerializer):
    class Meta:
        model = OrderProduct
        fields = ['product', 'quantity']


class OrderSerializer(MapFieldsModelSerializer):
    products = OrderProductSerializer(many=True, allow_empty=False, write_only=True)
    field_name_map = {
        'address': 'address',
        'first_name': 'firstname',
        'last_name': 'lastname',
        'contact_phone': 'phonenumber',
        'products': 'products'
    }

    class Meta:
        model = Order
        fields = ['address', 'first_name', 'last_name', 'contact_phone', 'products']
