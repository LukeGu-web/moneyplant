from django.core.mail import BadHeaderError
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.shortcuts import redirect

from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from user.models import Account
from user.utils import Util, EmailVerificationTokenGenerator


email_verification_token = EmailVerificationTokenGenerator()


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
            # Send push notification if expo_push_token is available
            if account.expo_push_token:
                Util.send_push_message(
                    token=account.expo_push_token,
                    message="Your email has been successfully verified!",
                    extra={"type": "EMAIL_VERIFIED"}
                )

            return redirect("https://getrich.lukegu.com/verification/")
        else:
            return redirect("https://getrich.lukegu.com/verification/failure/")


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
