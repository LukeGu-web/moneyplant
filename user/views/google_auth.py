from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from user.models import Account
from user.utils import Util
from book.serializers import BookSerializer
import requests as http_requests
import base64
import logging

# Set up logging
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    try:
        # Initialize book_data at the beginning
        book_data = None

        # Get the ID token and account_id from the request
        id_token_str = request.data.get('accessToken')
        account_id = request.data.get('account_id')

        if not id_token_str or not account_id:
            return Response({
                'error': 'Missing required fields: accessToken or account_id'
            }, status=status.HTTP_400_BAD_REQUEST)

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

        # First, check if a user exists with this Google social_id
        existing_google_account = Account.objects.filter(
            social_id=social_id,
            auth_provider='google'
        ).first()

        if existing_google_account:
            # User already exists with this Google account - login directly
            user = existing_google_account.user
            account = existing_google_account
            # Update user information
            user.first_name = idinfo.get('given_name', '')
            user.last_name = idinfo.get('family_name', '')
            user.save()

            account.nickname = name
            account.account_status = 'verified'
            account.save()
        else:
            # Check if a user exists with the same email but different provider
            user_with_same_email = User.objects.filter(email=email).first()
            if user_with_same_email:
                account = Account.objects.filter(
                    user=user_with_same_email).first()
                if account:
                    if account.auth_provider != 'google':
                        return Response({
                            'error': f'This email has already been registered with {account.auth_provider or "another provider"}.'
                        }, status=status.HTTP_400_BAD_REQUEST)

            # Check if the user exists with the provided account_id
            user = User.objects.filter(username=account_id).first()

            if not user:
                # First time login - Create new user with transaction
                try:
                    with transaction.atomic():
                        # Create user
                        user = User.objects.create(
                            username=account_id,
                            email=email,
                            first_name=idinfo.get('given_name', ''),
                            last_name=idinfo.get('family_name', '')
                        )

                        # Create account
                        account = Account.objects.create(
                            user=user,
                            account_id=account_id,
                            nickname=name,
                            account_status='verified',
                            auth_provider='google',
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
                                nickname=name,
                                account_status='verified',
                                auth_provider='google',
                                social_id=social_id
                            )
                        else:
                            if account.auth_provider is None:
                                # Update the account if auth_provider is None
                                account.auth_provider = 'google'
                                account.social_id = social_id
                                account.nickname = name
                                account.account_status = 'verified'
                                account.save()
                            elif account.auth_provider != 'google':
                                return Response({
                                    'error': f'This account is already registered with {account.auth_provider or "another provider"}.'
                                }, status=status.HTTP_400_BAD_REQUEST)
                            else:
                                # Update existing Google account information
                                account.social_id = social_id
                                account.nickname = name
                                account.account_status = 'verified'
                                account.save()
                except Exception as e:
                    logger.error(
                        f"Transaction failed during account update: {str(e)}")
                    return Response({
                        'error': 'Failed to update account information'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Update profile picture if available (outside transaction as it's not critical)
        if picture_url:
            try:
                response = http_requests.get(picture_url)
                if response.status_code == 200:
                    content_type = response.headers.get(
                        'content-type', 'image/jpeg')
                    image_base64 = base64.b64encode(
                        response.content).decode('utf-8')
                    base64_image = f"data:{content_type};base64,{image_base64}"
                    account.avatar = base64_image
                    account.save()
            except Exception as e:
                logger.error(f"Failed to update profile picture: {str(e)}")
                # Don't return error response as this is not critical

        # Get or create token
        token, _ = Token.objects.get_or_create(user=user)

        # Prepare response data
        response_data = {
            'id': account.id,
            'account_id': account.account_id,
            'avatar': account.avatar,
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
            'error': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error in google_auth: {str(e)}")
        return Response({
            'error': 'An unexpected error occurred'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
