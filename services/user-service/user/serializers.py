from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'is_customer', 'is_agent']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    token = serializers.CharField(read_only=True)
    is_customer = serializers.BooleanField(read_only=True)
    is_agent = serializers.BooleanField(read_only=True)
    is_admin = serializers.BooleanField(read_only=True)

    def validate(self, data):
        from django.contrib.auth import authenticate
        from rest_framework_jwt.settings import api_settings

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            raise serializers.ValidationError('Email and password required')

        user = authenticate(username=email, password=password)
        if not user:
            raise serializers.ValidationError('Invalid email or password')

        if user.is_agent and not user.is_approved:
            raise serializers.ValidationError('Agent not approved yet')

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        data['token'] = token
        data['is_customer'] = user.is_customer
        data['is_agent'] = user.is_agent
        data['is_admin'] = user.is_admin

        return data


class ListUserSerializer(serializers.ModelSerializer):
    """Serializer for listing users."""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_customer', 'is_agent', 'is_approved']


class CreateAdminSerializer(serializers.ModelSerializer):
    """Serializer for creating admin users."""
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        user = User.objects.create_user(
            is_admin=True,
            is_customer=False,
            is_agent=False,
            **validated_data
        )
        return user


class ApproveAgentSerializer(serializers.ModelSerializer):
    """Serializer for approving/rejecting agents."""
    class Meta:
        model = User
        fields = ['is_approved']
