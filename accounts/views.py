from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    UserRegistrationSerializer, 
    UserSerializer,
    LoginSerializer,
    TokenResponseSerializer
)
from rest_framework.views import APIView
User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegistrationSerializer


class UserDetailView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAdminUser,)


class LoginView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # The validated_data contains user and tokens due to our LoginSerializer implementation
        validated_data = serializer.validated_data
        
        response_serializer = TokenResponseSerializer({
            'access': validated_data['access'],
            'refresh': validated_data['refresh'],
            'user': validated_data['user']
        })

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'detail': 'No refresh token provided.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            RefreshToken(refresh_token).blacklist()
            return Response(
                {'detail': 'Successfully logged out.'}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            print(e)
            return Response(
                {'detail': 'Invalid token.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
