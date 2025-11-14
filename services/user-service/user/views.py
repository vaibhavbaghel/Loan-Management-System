from django.http import Http404
from django.db.models import Q

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.settings import api_settings
from rest_framework.exceptions import ValidationError

from .models import User
from .serializers import (
    UserSerializer, LoginSerializer, ListUserSerializer,
    CreateAdminSerializer, ApproveAgentSerializer
)
from .permissions import IsAdmin, IsAdminOrAgent

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class UserSignupView(APIView):
    """
    POST /api/user/signup/
    Register a new user (customer or agent).
    """
    permission_classes = (AllowAny,)

    def post(self, request):
        user_serializer = UserSerializer(data=request.data)
        if not user_serializer.is_valid():
            response = {
                'success': False,
                'message': 'This account already exists',
                'errors': user_serializer.errors
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
        user_serializer.save()
        user = User.objects.get(email=request.data['email'])
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        response = {
            'success': True,
            'message': 'User registered successfully',
            'token': token
        }
        return Response(response, status=status.HTTP_201_CREATED)


class UserLoginView(APIView):
    """
    POST /api/user/login/
    Authenticate user and return JWT token.
    """
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            response = {
                'success': True,
                'message': 'User logged in successfully',
                'token': serializer.data['token'],
                'is_customer': serializer.data['is_customer'],
                'is_agent': serializer.data['is_agent'],
                'is_admin': serializer.data['is_admin']
            }
            return Response(response, status=status.HTTP_200_OK)
        except ValidationError as e:
            response = {
                'success': False,
                'message': str(e.detail[0]) if e.detail else 'Login failed'
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    GET /api/user/profile/
    Retrieve authenticated user's profile.
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication,)

    def get(self, request):
        try:
            user = request.user
            response = {
                'success': True,
                'message': 'Profile fetched',
                'data': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_customer': user.is_customer,
                    'is_agent': user.is_agent,
                    'is_admin': user.is_admin,
                    'is_approved': user.is_approved,
                    'last_login': user.last_login,
                    'date_joined': user.date_joined
                }
            }
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response = {
                'success': False,
                'message': 'Could not fetch profile',
                'error': str(e)
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class CreateAdminView(APIView):
    """
    POST /api/user/create-admin/
    Create a new admin user (admin-only).
    """
    permission_classes = (IsAuthenticated, IsAdmin,)
    authentication_classes = (JSONWebTokenAuthentication,)

    def post(self, request):
        user_serializer = CreateAdminSerializer(data=request.data)
        if not user_serializer.is_valid():
            response = {
                'success': False,
                'message': 'This account already exists',
                'errors': user_serializer.errors
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
        user_serializer.save()
        response = {
            'success': True,
            'message': 'Admin registered successfully',
        }
        return Response(response, status=status.HTTP_201_CREATED)


class ListAgentCustomersView(generics.ListAPIView):
    """
    GET /api/user/list-agents/
    List customers (for agents and admins).
    """
    permission_classes = (IsAuthenticated, IsAdminOrAgent,)
    authentication_classes = (JSONWebTokenAuthentication,)
    serializer_class = ListUserSerializer
    queryset = User.objects.filter(is_customer=True)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })


class ListAdminUsersView(generics.ListAPIView):
    """
    GET /api/user/list-users/
    List users (for admins).
    """
    permission_classes = (IsAuthenticated, IsAdmin,)
    authentication_classes = (JSONWebTokenAuthentication,)
    serializer_class = ListUserSerializer
    queryset = User.objects.filter(Q(is_customer=True) | Q(is_agent=True))

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })


class ListPendingApprovalsView(generics.ListAPIView):
    """
    GET /api/user/list-approvals/
    List pending agent approvals (admin-only).
    """
    permission_classes = (IsAuthenticated, IsAdmin,)
    authentication_classes = (JSONWebTokenAuthentication,)
    serializer_class = ListUserSerializer
    queryset = User.objects.filter(is_agent=True, is_approved=False)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })


class ApproveOrDeleteAgentView(APIView):
    """
    PUT /api/user/approve-delete/<int:pk>/
    Approve or delete an agent (admin-only).
    DELETE /api/user/approve-delete/<int:pk>/
    Delete an agent.
    """
    permission_classes = (IsAuthenticated, IsAdmin,)
    authentication_classes = (JSONWebTokenAuthentication,)

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404('User not found')

    def put(self, request, pk):
        instance = self.get_object(pk)
        serializer = ApproveAgentSerializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            response = {
                "success": True,
                "message": f"Agent id {pk} has been approved"
            }
            return Response(response, status=status.HTTP_200_OK)
        response = {
            "success": False,
            "message": "Could not approve agent",
            "errors": serializer.errors
        }
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        instance = self.get_object(pk)
        try:
            instance.delete()
            response = {
                "success": True,
                "message": f"Agent id {pk} has been deleted"
            }
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response = {
                "success": False,
                "message": "Could not delete agent",
                "error": str(e)
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
