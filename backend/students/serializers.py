from rest_framework import serializers
from .models import StudentProfile
import re

class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ['date_of_birth', 'gender', 'mobile_number', 'address', 'category', 'domicile_state']

    def validate_mobile_number(self, value):
        if not re.match(r'^\+?1?\d{9,15}$', value):
            raise serializers.ValidationError("Invalid mobile number format.")
        return value

    def validate_address(self, value):
        required_keys = {'street', 'city', 'state', 'pincode'}
        if not isinstance(value, dict) or not required_keys.issubset(value.keys()):
            raise serializers.ValidationError("Address must contain street, city, state, and pincode.")
        return value
