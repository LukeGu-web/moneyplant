from django.core.mail import BadHeaderError
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.shortcuts import redirect

from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics

from .serializers import AccountSerializer
from .models import Account
from .permissions import IsOwner
from .utils import Util, EmailVerificationTokenGenerator
# from rest_framework_simplejwt.tokens import RefreshToken

email_verification_token = EmailVerificationTokenGenerator()


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

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user_data = request.data.get('user', {})
        new_password = user_data.get('password')
        account_status = request.data.get('account_status')

        # Handle password change explicitly
        if new_password:
            instance.user.set_password(new_password)
            instance.user.save()
            print(f"Password updated for user {instance.user.username}")
            print(f"New password hash: {instance.user.password}")
            print(f"account_status: {account_status}")
            if account_status == 'registered':
                # Send verification email
                token = email_verification_token.make_token(instance.user)
                uid = urlsafe_base64_encode(force_bytes(instance.user.pk))
                current_site = get_current_site(request)
                verification_link = reverse('verify_email', kwargs={
                                            'uidb64': uid, 'token': token})
                verification_url = f"http://{
                    current_site.domain}{verification_link}"
                print(f"email: {instance.user.email}")
                print(f"verification_url: {verification_url}")
                Util.send_email({
                    "email_subject": 'Verify your email address',
                    "email_body": f'Click the link to verify your email: {verification_url}',
                    "to_email": instance.user.email,
                })

        # Update the remaining fields
        # Exclude the password from serializer data to avoid re-hashing
        if 'user' in request.data and 'password' in request.data['user']:
            request.data['user'].pop('password')

        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)


class VerifyEmail(APIView):
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and email_verification_token.check_token(user, token):
            # Email verified successfully, update account_status
            account = Account.objects.get(user=user)
            account.account_status = "verified"
            account.save()
            return redirect("https://getrich-web.netlify.app/verification/")
        else:
            return redirect("https://getrich-web.netlify.app/verification/failure/")


@api_view(["POST"])
def send_verification_email(request):
    if request.method == "POST":
        try:
            user = Token.objects.get(key=request.auth.key).user
            token = email_verification_token.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            current_site = get_current_site(request)
            verification_link = reverse('verify_email', kwargs={
                                        'uidb64': uid, 'token': token})
            verification_url = f"http://{
                current_site.domain}{verification_link}"
            print(f"email: {user.email}")
            print(f"verification_url: {verification_url}")
            Util.send_email({
                "email_subject": 'Verify your email address',
                "email_body": f'Click the link to verify your email: {verification_url}',
                "to_email": user.email,
            })
        except BadHeaderError:
            return Response({"error": "Invalid header found."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"details": "Send successfully."}, status=status.HTTP_200_OK)


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

        if serializer.is_valid(raise_exception=True):
            # Extract user data from the validated data
            user_data = serializer.validated_data.pop('user')

            # Create the User instance
            user = User.objects.create_user(**user_data)

            # Create the Account instance with the associated User
            account = Account.objects.create(
                user=user, **serializer.validated_data)

            # Authenticate the user and generate a token
            user = authenticate(
                username=user_data['username'], password=user_data['password'])

            if user:
                token, created = Token.objects.get_or_create(user=user)
                data = {
                    # Serialize the account data
                    'account': AccountSerializer(account).data,
                    'token': token.key  # Include the authentication token
                }
                return Response(data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {"detail": "Authentication failed."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(http_method_names=["GET"])
def user_details_view(request):
    if request.method == "GET":
        try:
            user = Token.objects.get(key=request.auth.key).user
            account = Account.objects.get(user=user)
            serializer = AccountSerializer(account)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Token.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)


# @api_view(["POST"])
# def logout_user(request):
#     if request.method == "POST":
#         request.user.auth_token.delete()
#         return Response({"message": "You are logged out"}, status=status.HTTP_200_OK)
