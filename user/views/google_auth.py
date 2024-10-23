# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from django.contrib.auth.models import User
from user.models import Account
import uuid
import requests as http_requests
import base64


@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    try:
        # Get the ID token from the request
        id_token_str = request.data.get('accessToken')
        # Optional: if you're sending this from frontend
        account_id = request.data.get('account_id')

        # Verify the ID token
        idinfo = id_token.verify_oauth2_token(
            id_token_str,
            requests.Request(),
            settings.SOCIAL_AUTH_GOOGLE_CLIENT_ID
        )

        # Get user info from the token
        email = idinfo['email']
        name = idinfo['name']
        social_id = idinfo['sub']
        picture_url = idinfo.get('picture')

        # Check if user exists
        user = User.objects.filter(email=email).first()

        if not user:
            # Create new user
            username = email  # or generate a unique username
            user = User.objects.create(
                username=username,
                email=email,
                first_name=idinfo.get('given_name', ''),
                last_name=idinfo.get('family_name', '')
            )

            # Generate account_id if not provided
            if not account_id:
                account_id = f"ACC{uuid.uuid4().hex[:10].upper()}"

            # Create Account
            account = Account.objects.create(
                user=user,
                account_id=account_id,
                nickname=name,
                account_status='verified',
                auth_provider='google',
                social_id=social_id
            )

            # Download and save profile picture if available
            if picture_url:
                response = http_requests.get(picture_url)
                if response.status_code == 200:
                    account.avatar = response.content
                    account.save()

        else:
            # Get or create account for existing user
            account, created = Account.objects.get_or_create(
                user=user,
                defaults={
                    'account_id': account_id or f"ACC{uuid.uuid4().hex[:10].upper()}",
                    'nickname': name,
                    'account_status': 'verified',
                    'auth_provider': 'google',
                    'social_id': social_id
                }
            )

            # Update existing account if needed
            if not created:
                account.nickname = name
                account.auth_provider = 'google'
                account.social_id = social_id
                account.account_status = 'verified'
                account.save()

        # Get or create token
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'id': account.id,
            'account_id': account.account_id,
            'avatar': base64.b64encode(account.avatar).decode('utf-8') if account.avatar else None,
            'nickname': account.nickname,
            'account_status': account.account_status,
            'email': user.email,
            'date_joined': user.date_joined,
            'token': token.key
        })

    except ValueError:
        # Invalid token
        return Response({
            'error': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        # Handle other errors
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
