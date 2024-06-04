from django.shortcuts import render
from django.http import Http404
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from .serializers import DeviceRegisterSerializer, UserRegisterSerializer
# from rest_framework_simplejwt.tokens import RefreshToken
import json


class UserDetail(APIView):
    """
    Retrieve, update or delete a User instance.
    """

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        User = self.get_object(pk)
        serializer = UserRegisterSerializer(User)
        return Response(serializer.data)

    # def put(self, request, pk, format=None):
    #     User = self.get_object(pk)
    #     serializer = UserRegisterSerializer(User, data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def delete(self, request, pk, format=None):
    #     User = self.get_object(pk)
    #     User.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(http_method_names=["POST"])
def device_register_view(request):
    if request.method == "POST":

        serializer = DeviceRegisterSerializer(data=request.data)

        if serializer.is_valid(raise_exception=ValueError):
            account = serializer.create(validated_data=request.data)
            data = account | {'message': 'Account has been created'}
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.error_messages, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def logout_user(request):
    if request.method == "POST":
        request.user.auth_token.delete()
        return Response({"Message": "You are logged out"}, status=status.HTTP_200_OK)


@api_view(http_method_names=["POST"])
def user_register_view(request):
    if request.method == "POST":
        serializer = UserRegisterSerializer(data=request.data)

        data = {}

        if serializer.is_valid():
            account = serializer.save()

            data['response'] = 'Account has been created'
            # data['username'] = account.username
            # data['email'] = account.email

            # token = Token.objects.get(user=account).key
            # data['token'] = token

            # refresh = RefreshToken.for_user(account)
            # data['token'] = {
            #     'refresh': str(refresh),
            #     'access': str(refresh.access_token)
            # }
        else:
            data = serializer.errors
        return Response(data)
