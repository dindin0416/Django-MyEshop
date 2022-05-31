import re

from django.core.exceptions import ValidationError
from rest_framework import serializers


def validate_file_size(file):
    max_size_kb = 10
    if file.size > max_size_kb * 1024 * 1024:
        raise ValidationError(f'Files cannot be larger than {max_size_kb}MB!.')

def validate_product_title_no_fuck(value):
    if 'fuck' in value.lower():
        raise serializers.ValidationError("fuck is not allowed.")
    return value

def validate_phone(value):
    if len(value) == 10 and re.match(r'09\d{1}', value) and value.isdigit():
        return value
    else:
        raise serializers.ValidationError("Please enter a valid phone number.")
