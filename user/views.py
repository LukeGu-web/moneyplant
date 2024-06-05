from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import AccountSerializer
from .models import Account
# from rest_framework_simplejwt.tokens import RefreshToken


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


class AccountDetail(APIView):
    """
    Retrieve, update or delete a User instance.
    """

    def get(self, request, pk):
        account = Account.objects.get(pk=pk)
        serializer = AccountSerializer(account)
        return Response(serializer.data, status=status.HTTP_200_OK)

# update account details (user register)
    def put(self, request, pk, format=None):
        account = Account.objects.get(pk=pk)
        serializer = AccountSerializer(
            account, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            result = {'message': 'Account details has been updated',
                      'id': account.id}
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.error_messages, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        account = Account.objects.get(pk=pk)
        account.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
def logout_user(request):
    if request.method == "POST":
        request.user.auth_token.delete()
        return Response({"message": "You are logged out"}, status=status.HTTP_200_OK)
