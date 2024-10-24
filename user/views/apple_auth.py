from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from user.models import Account
from user.utils import Util
from book.serializers import BookSerializer
import jwt
import requests
import uuid
import json
from jwt.algorithms import RSAAlgorithm


@api_view(['POST'])
@permission_classes([AllowAny])
def apple_auth(request):
    try:
        # Get the identity token from request
        identity_token = request.data.get('accessToken')
        account_id = request.data.get('account_id')

        if not identity_token:
            return Response({
                'error': 'Identity token is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Fetch Apple's public keys
        keys_response = requests.get('https://appleid.apple.com/auth/keys')
        keys = keys_response.json()['keys']

        # Get the kid (Key ID) from the token headers
        token_headers = jwt.get_unverified_header(identity_token)
        token_kid = token_headers.get('kid')

        # Find the matching public key
        public_key = None
        for key in keys:
            if key['kid'] == token_kid:
                # Convert the JWK to PEM format
                public_key = RSAAlgorithm.from_jwk(json.dumps(key))
                break

        if not public_key:
            return Response({
                'error': 'No matching key found'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify and decode the token
        try:
            decoded_token = jwt.decode(
                identity_token,
                public_key,
                algorithms=['RS256'],
                audience='com.lukeguexpo.moneymongoose',  # Your app's bundle ID
                issuer='https://appleid.apple.com'
            )
        except jwt.InvalidTokenError as e:
            return Response({
                'error': f'Invalid token: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Extract user info
        social_id = decoded_token.get('sub')  # Apple user ID
        email = decoded_token.get('email')
        email_verified = decoded_token.get('email_verified', False)

        if not email:
            email = f"{social_id}@private.apple.com"

        # Check if a user exists with the same email but different provider
        user_with_same_email = User.objects.filter(email=email).first()
        if user_with_same_email:
            account = Account.objects.filter(user=user_with_same_email).first()
            if account and account.auth_provider != 'apple':
                return Response({
                    'error': f'This email has already been registered with {account.auth_provider}.'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user exists with the same account_id
        user = User.objects.filter(
            username=account_id).first() if account_id else None
        book_data = None

        if not user:
            # First time login - Create new user
            if not account_id:
                account_id = f"ACC{uuid.uuid4().hex[:10].upper()}"

            user = User.objects.create(
                username=account_id,
                email=email
            )

            # Create a new Account associated with Apple
            account = Account.objects.create(
                user=user,
                account_id=account_id,
                nickname=email.split('@')[0],
                account_status='verified' if email_verified else 'pending',
                auth_provider='apple',
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
                    nickname=email.split('@')[0],
                    account_status='verified' if email_verified else 'pending',
                    auth_provider='apple',
                    social_id=social_id
                )
            elif account.auth_provider != 'apple':
                # User exists with different auth provider
                return Response({
                    'error': f'This account is already registered with {account.auth_provider}.'
                }, status=status.HTTP_400_BAD_REQUEST)
            elif account.social_id != social_id:
                # Different Apple account trying to use same account_id
                return Response({
                    'error': 'This account is already linked to a different Apple account.'
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Update existing Apple account information
                account.account_status = 'verified' if email_verified else 'pending'
                account.save()

                # Note: We don't update the email for existing Apple users
                # as Apple may provide a private relay email

        # Get or create token
        token, _ = Token.objects.get_or_create(user=user)

        response_data = {
            'id': account.id,
            'account_id': account.account_id,
            'avatar': None,  # Apple doesn't provide avatar
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
            'error': 'Invalid token format'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
