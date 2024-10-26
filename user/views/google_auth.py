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
from user.utils import Util
from book.serializers import BookSerializer
import uuid
import requests as http_requests
import base64


@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    try:
        # Get the ID token and account_id from the request
        id_token_str = request.data.get('accessToken')
        account_id = request.data.get('account_id')

        # Verify the ID token with Google
        idinfo = id_token.verify_oauth2_token(
            id_token_str,
            requests.Request(),
            settings.SOCIAL_AUTH_GOOGLE_CLIENT_ID
        )

        # Extract user info from the token
        email = idinfo['email']
        name = idinfo['name']
        social_id = idinfo['sub']
        picture_url = idinfo.get('picture')

        # Check if a user exists with the same email but different provider
        user_with_same_email = User.objects.filter(email=email).first()
        if user_with_same_email:
            account = Account.objects.filter(user=user_with_same_email).first()
            if account and account.auth_provider != 'google':
                return Response({
                    'error': f'This email has already been registered with {account.auth_provider}.'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user exists with the same account_id
        user = User.objects.filter(username=account_id).first()
        book_data = None

        if not user:
            # First time login - Create new user
            user = User.objects.create(
                username=account_id,
                email=email,
                first_name=idinfo.get('given_name', ''),
                last_name=idinfo.get('family_name', '')
            )

            # Create a new Account associated with Google
            account = Account.objects.create(
                user=user,
                account_id=account_id,
                nickname=name,
                account_status='verified',
                auth_provider='google',
                social_id=social_id
            )

            # Create default book and groups for first-time users
            book, groups = Util.create_default_book_with_groups(user)
            book_serializer = BookSerializer(book)
            book_data = book_serializer.data

        else:
            # User exists with this account_id
            account = Account.objects.filter(user=user).first()

            if not account:
                # User exists but no account - Create new account
                account = Account.objects.create(
                    user=user,
                    account_id=account_id,
                    nickname=name,
                    account_status='verified',
                    auth_provider='google',
                    social_id=social_id
                )
            elif account.auth_provider != 'google':
                # User exists with different auth provider
                return Response({
                    'error': f'This account is already registered with {account.auth_provider}.'
                }, status=status.HTTP_400_BAD_REQUEST)
            elif account.social_id != social_id:
                # Different Google account trying to use same account_id
                return Response({
                    'error': 'This account is already linked to a different Google account.'
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Update existing Google account information
                user.first_name = idinfo.get('given_name', '')
                user.last_name = idinfo.get('family_name', '')
                user.save()

                account.nickname = name
                account.account_status = 'verified'
                account.save()

        # Update profile picture if available
        if picture_url:
            try:
                response = requests.get(picture_url)
                if response.status_code == 200:
                    account.avatar = response.content
                    account.save()
            except Exception as e:
                # Log the error but don't fail the authentication
                print(f"Failed to update profile picture: {str(e)}")

        # Get or create token
        token, _ = Token.objects.get_or_create(user=user)

        # Properly handle the avatar encoding
        avatar_data = None
        if account.avatar:
            try:
                # Encode binary data directly to base64 without UTF-8 decoding
                avatar_data = base64.b64encode(account.avatar).decode('ascii')
            except Exception as e:
                print(f"Failed to encode avatar: {str(e)}")

        response_data = {
            'id': account.id,
            'account_id': account.account_id,
            'avatar': avatar_data,
            'nickname': account.nickname,
            'account_status': account.account_status,
            'email': user.email,
            'date_joined': user.date_joined,
            'token': token.key,
        }

        if book_data:
            response_data['book'] = book_data

        return Response(response_data)

    except ValueError:
        return Response({
            'error': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
