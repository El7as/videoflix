from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers



User = get_user_model()



class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer used for user registration.

    Responsibilities:
    - Validate password + confirmed_password match
    - Apply Django's built‑in password validators
    - Create a new inactive user (activation required)
    """
        
    confirmed_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['email', 'password', 'confirmed_password']


    def validate(self, data):
        """
        Ensure both password fields match.
        """
                
        if data['password'] != data['confirmed_password']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return data


    def create(self, validated_data):
        """
        Create a new inactive user.

        Steps:
        1. Remove confirmed_password (not stored in DB)
        2. Extract email + password
        3. Create user with username derived from email prefix
        4. Mark user as inactive until email activation
        """

        validated_data.pop('confirmed_password')
        email = validated_data['email']
        password = validated_data['password']

        user = User.objects.create_user(username=email.split('@')[0], email=email, password=password)
        user.is_active = False
        user.save()
        return user



class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer used to validate password reset confirmation input.

    Responsibilities:
    - Ensure both password fields are provided
    - Ensure they match
    - Enforce minimum length (handled by CharField)
    """

    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        """
        Validate the new password using Django's built-in validators.
        """
        try:
            validate_password(value)
        except serializers.ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value


    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'detail': 'Passwords do not match.'})
        return attrs

