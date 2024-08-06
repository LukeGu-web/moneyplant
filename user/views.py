from django.http import Http404
from django.core.mail import BadHeaderError
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import AccountSerializer
from .models import Account
from .permissions import IsOwnerOrReadonly, IsOwner
from .utils import Util
# from rest_framework_simplejwt.tokens import RefreshToken


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


@api_view(http_method_names=["POST"])
def send_email_view(request):
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
            data = account | {'message': 'Account has been created'}
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


class AccountDetail(APIView):
    """
    Retrieve, update or delete a User instance.
    """
    permission_classes = [IsOwner]

    def get_object(self, pk):
        try:
            return Account.objects.get(pk=pk)
        except Account.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        account = self.get_object(pk)
        serializer = AccountSerializer(account)
        return Response(serializer.data, status=status.HTTP_200_OK)

# update account details (user register)
    def put(self, request, pk, format=None):
        account = self.get_object(pk)
        if account.user != request.user:
            return Response({'error': 'Wrong credential'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = AccountSerializer(
            account, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            result = {'message': 'Account details has been updated',
                      'id': account.id}
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.error_messages, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        account = self.get_object(pk)
        if account.user != request.user:
            return Response({'error': 'Wrong credential'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            account.delete()
            return Response({'message': 'Delete successfully'}, status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
def logout_user(request):
    if request.method == "POST":
        request.user.auth_token.delete()
        return Response({"message": "You are logged out"}, status=status.HTTP_200_OK)
