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
        # Get the ID token from the request
        id_token_str = request.data.get('accessToken')
        account_id = request.data.get('account_id')

        # Verify the ID token
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

        # Check if user exists
        user = User.objects.filter(email=email).first()
        is_first_time = False
        book_data = None

        if not user:
            # First-time user flow
            is_first_time = True

            # Create new user
            username = email
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

            # Create default book and groups for first-time users
            book, groups = Util.create_default_book_with_groups(user)

            # Serialize book data for response
            book_serializer = BookSerializer(book)
            book_data = book_serializer.data

        else:
            # Returning user flow
            account = Account.objects.filter(user=user).first()

            if not account:
                # Edge case: User exists but no account (shouldn't normally happen)
                account = Account.objects.create(
                    user=user,
                    account_id=account_id or f"ACC{
                        uuid.uuid4().hex[:10].upper()}",
                    nickname=name,
                    account_status='verified',
                    auth_provider='google',
                    social_id=social_id
                )
            else:
                # Update existing account
                account.nickname = name
                account.auth_provider = 'google'
                account.social_id = social_id
                account.account_status = 'verified'
                account.save()

        # Get or create token
        token, _ = Token.objects.get_or_create(user=user)

        response_data = {
            'id': account.id,
            'account_id': account.account_id,
            'avatar': base64.b64encode(account.avatar).decode('utf-8') if account.avatar else None,
            'nickname': account.nickname,
            'account_status': account.account_status,
            'email': user.email,
            'date_joined': user.date_joined,
            'token': token.key,
            'is_first_time': is_first_time
        }

        # Include book data for first-time users
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
