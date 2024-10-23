# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.conf import settings
from django.contrib.auth.models import User
from user.models import Account
import requests
import uuid
import base64


@api_view(['POST'])
@permission_classes([AllowAny])
def facebook_auth(request):
    try:
        access_token = request.data.get('accessToken')
        account_id = request.data.get('account_id')  # Optional

        # Verify and get user data from Facebook
        graph_api_url = f"https://graph.facebook.com/v18.0/me"
        params = {
            'fields': 'id,name,email,first_name,last_name,picture.type(large)',
            'access_token': access_token
        }

        fb_response = requests.get(graph_api_url, params=params)
        fb_data = fb_response.json()

        if 'error' in fb_data:
            return Response({
                'error': 'Invalid Facebook token'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Extract user info
        email = fb_data.get('email')
        name = fb_data.get('name')
        social_id = fb_data.get('id')
        picture_url = fb_data.get('picture', {}).get('data', {}).get('url')

        # If email is not provided by Facebook (rare case)
        if not email:
            email = f"{social_id}@facebook.com"

        # Check if user exists
        user = User.objects.filter(email=email).first()

        if not user:
            # Create new user
            username = email  # or generate a unique username
            user = User.objects.create(
                username=username,
                email=email,
                first_name=fb_data.get('first_name', ''),
                last_name=fb_data.get('last_name', '')
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
                auth_provider='facebook',
                social_id=social_id
            )

            # Download and save profile picture if available
            if picture_url:
                response = requests.get(picture_url)
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
                    'auth_provider': 'facebook',
                    'social_id': social_id
                }
            )

            # Update existing account if needed
            if not created:
                account.nickname = name
                account.auth_provider = 'facebook'
                account.social_id = social_id
                account.account_status = 'verified'

                # Update profile picture
                if picture_url:
                    response = requests.get(picture_url)
                    if response.status_code == 200:
                        account.avatar = response.content
                account.save()

        # Get or create token
        token, _ = Token.objects.get_or_create(user=user)

        # Return response in the same structure as Google login
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

    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
