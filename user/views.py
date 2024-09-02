from django.http import Http404
from django.core.mail import BadHeaderError
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics

from .serializers import AccountSerializer
from .models import Account
from .permissions import IsOwnerOrReadonly, IsOwner
from .utils import Util
# from rest_framework_simplejwt.tokens import RefreshToken


class AccountDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a Account instance.
    """
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        """
        Optionally restricts the returned accounts to the user who is the owner.
        """
        user = self.request.user
        return Account.objects.filter(user=user)


@api_view(http_method_names=["POST"])
def tax_return_view(request):
    if request.method == "POST":
        try:
            Util.send_email({
                "email_subject": 'With attachment',
                "email_body": 'Hello world',
                "to_email": 'mythnan@gmail.com',
                'email_attachment': 'doc/new.pdf'
            })
        except BadHeaderError:
            return Response({"error": "Invalid header found."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"details": "Send successfully."}, status=status.HTTP_200_OK)

    if request.method == "POST":
        try:
            Util.send_email({
                "email_subject": 'No attachment',
                "email_body": 'Hello world',
                "to_email": 'mythnan@gmail.com',
            })
        except BadHeaderError:
            return Response({"error": "Invalid header found."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"details": "Send successfully."}, status=status.HTTP_200_OK)


@api_view(http_method_names=["POST"])
def fill_pdf_view(request):
    if request.method == "POST":
        try:
            Util.fill_pdf()
        except BadHeaderError:
            return Response({"error": "Invalid file."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"details": "Send successfully."}, status=status.HTTP_200_OK)


@api_view(http_method_names=["POST"])
def device_register_view(request):
    if request.method == "POST":

        serializer = AccountSerializer(data=request.data)

        if serializer.is_valid(raise_exception=ValueError):
            account = serializer.create(validated_data=request.data)
            user = authenticate(
                username=request.data['user']['username'], password=request.data['user']['password'])
            token = Token.objects.get(user=user)
            data = account | {'token': token.key}
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.error_messages, status=status.HTTP_400_BAD_REQUEST)


@api_view(http_method_names=["GET"])
def user_details_view(request):
    if request.method == "GET":
        try:
            user = Token.objects.get(key=request.auth.key).user
            account = Account.objects.get(user=user)
            serializer = AccountSerializer(account)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Token.DoesNotExist:
            raise Http404


@api_view(["POST"])
def logout_user(request):
    if request.method == "POST":
        request.user.auth_token.delete()
        return Response({"message": "You are logged out"}, status=status.HTTP_200_OK)
