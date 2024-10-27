from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.db import transaction
from user.models import Account
from user.utils import Util
from book.serializers import BookSerializer
import jwt
import requests
import uuid
import json
import logging
from jwt.algorithms import RSAAlgorithm

# Set up logging
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def apple_auth(request):
    try:
        # Initialize book_data at the beginning
        book_data = None

        # Get the identity token from request
        identity_token = request.data.get('accessToken')
        account_id = request.data.get('account_id')

        if not identity_token:
            return Response({
                'error': 'Identity token is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
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
                logger.error("No matching Apple public key found")
                return Response({
                    'error': 'No matching key found'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Verify and decode the token
            decoded_token = jwt.decode(
                identity_token,
                public_key,
                algorithms=['RS256'],
                audience='com.lukeguexpo.moneymongoose',  # Your app's bundle ID
                issuer='https://appleid.apple.com'
            )
        except jwt.InvalidTokenError as e:
            logger.error(f"Apple JWT validation error: {str(e)}")
            return Response({
                'error': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)
        except requests.RequestException as e:
            logger.error(f"Failed to fetch Apple public keys: {str(e)}")
            return Response({
                'error': 'Failed to verify Apple token'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Extract user info
        social_id = decoded_token.get('sub')  # Apple user ID
        email = decoded_token.get('email')
        email_verified = decoded_token.get('email_verified', False)

        if not email:
            email = f"{social_id}@private.apple.com"

        # First, check if a user exists with this Apple social_id
        existing_apple_account = Account.objects.filter(
            social_id=social_id,
            auth_provider='apple'
        ).first()

        if existing_apple_account:
            # User already exists with this Apple account - login directly
            user = existing_apple_account.user
            account = existing_apple_account

            # Update account status if email verification status changed
            if account.account_status != ('verified' if email_verified else 'pending'):
                account.account_status = 'verified' if email_verified else 'pending'
                account.save()
        else:
            # Check if a user exists with the same email but different provider
            user_with_same_email = User.objects.filter(email=email).first()
            if user_with_same_email:
                account = Account.objects.filter(
                    user=user_with_same_email).first()
                if account:
                    if account.auth_provider != 'apple':
                        return Response({
                            'error': f'This email has already been registered with {account.auth_provider or "another provider"}.'
                        }, status=status.HTTP_400_BAD_REQUEST)

            # Check if the user exists with the provided account_id
            user = User.objects.filter(
                username=account_id).first() if account_id else None

            if not user:
                # First time login - Create new user with transaction
                try:
                    with transaction.atomic():
                        # Generate account_id if not provided
                        if not account_id:
                            account_id = f"ACC{uuid.uuid4().hex[:10].upper()}"

                        # Create user
                        user = User.objects.create(
                            username=account_id,
                            email=email
                        )

                        # Create account
                        account = Account.objects.create(
                            user=user,
                            account_id=account_id,
                            nickname=email.split('@')[0],
                            account_status='verified' if email_verified else 'pending',
                            auth_provider='apple',
                            social_id=social_id
                        )

                        # Create default book and groups
                        try:
                            book, groups = Util.create_default_book_with_groups(
                                user)
                            book_serializer = BookSerializer(book)
                            book_data = book_serializer.data
                        except Exception as e:
                            logger.error(
                                f"Failed to create default book and groups: {str(e)}")
                            # This will trigger rollback of the entire transaction
                            raise
                except Exception as e:
                    logger.error(
                        f"Transaction failed during user creation: {str(e)}")
                    return Response({
                        'error': 'Failed to create user account and associated data'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                # User exists with this account_id
                try:
                    with transaction.atomic():
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
                        else:
                            if account.auth_provider is None:
                                # Update the account if auth_provider is None
                                account.auth_provider = 'apple'
                                account.social_id = social_id
                                account.nickname = email.split('@')[0]
                                account.account_status = 'verified' if email_verified else 'pending'
                                account.save()
                            elif account.auth_provider != 'apple':
                                return Response({
                                    'error': f'This account is already registered with {account.auth_provider or "another provider"}.'
                                }, status=status.HTTP_400_BAD_REQUEST)
                            elif account.social_id != social_id:
                                return Response({
                                    'error': 'This account is already linked to a different Apple account.'
                                }, status=status.HTTP_400_BAD_REQUEST)
                            else:
                                # Update existing Apple account information
                                account.account_status = 'verified' if email_verified else 'pending'
                                account.save()
                except Exception as e:
                    logger.error(
                        f"Transaction failed during account update: {str(e)}")
                    return Response({
                        'error': 'Failed to update account information'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Get or create token
        token, _ = Token.objects.get_or_create(user=user)

        # Prepare response data
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

        # Only add book_data if it exists
        if book_data is not None:
            response_data['book'] = book_data

        return Response(response_data)

    except ValueError:
        return Response({
            'error': 'Invalid token format'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error in apple_auth: {str(e)}")
        return Response({
            'error': 'An unexpected error occurred'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
