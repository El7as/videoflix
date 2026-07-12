from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers



User = get_user_model()



class RegisterSerializer(serializers.ModelSerializer):
    confirmed_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['email', 'password', 'confirmed_password']


    def validate(self, data):
        if data['password'] != data['confirmed_password']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return data


    def create(self, validated_data):
        validated_data.pop('confirmed_password')
        email = validated_data['email']
        password = validated_data['password']

        user = User.objects.create_user(username=email.split('@')[0], email=email, password=password)
        user.is_active = False
        user.save()
        return user



class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'detail': 'Passwords do not match.'})
        return attrs

