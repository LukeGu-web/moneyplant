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
import requests
import uuid
import base64
import logging
import jwt

# Set up logging
logger = logging.getLogger(__name__)


def decode_limited_login_token(token):
    """
    Decode the Limited Login JWT token without verification
    to extract user information
    """
    try:
        # Decode without verification since we trust the token from the client
        decoded_token = jwt.decode(token, options={"verify_signature": False})

        # Map JWT claims to Facebook-like response
        return {
            # Facebook user ID is in 'sub' claim
            'id': decoded_token.get('sub'),
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name'),
            'first_name': decoded_token.get('given_name'),
            'last_name': decoded_token.get('family_name'),
            'picture': {
                'data': {
                    'url': decoded_token.get('picture')
                }
            }
        }
    except jwt.InvalidTokenError as e:
        logger.error(f"Error decoding token: {str(e)}")
        raise ValueError("Invalid token format")


@api_view(['POST'])
@permission_classes([AllowAny])
def facebook_auth(request):
    try:
        # Initialize book_data at the beginning
        book_data = None

        # Get request data
        access_token = request.data.get('accessToken')
        account_id = request.data.get('account_id')

        if not access_token:
            return Response({
                'error': 'Missing required field: accessToken'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Decode the Limited Login JWT token
            fb_data = decode_limited_login_token(access_token)
        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        # Extract user info from decoded token
        email = fb_data.get('email')
        name = fb_data.get('name')
        social_id = fb_data.get('id')
        picture_url = fb_data.get('picture', {}).get('data', {}).get('url')

        # For Limited Login, email might not be available
        if not email:
            # Generate a placeholder email using social_id
            email = f"{social_id}@facebook.com"

        # First, check if a user exists with this Facebook social_id
        existing_facebook_account = Account.objects.filter(
            social_id=social_id,
            auth_provider='facebook'
        ).first()

        if existing_facebook_account:
            # User already exists with this Facebook account - login directly
            user = existing_facebook_account.user
            account = existing_facebook_account

            # Update user information if available
            if fb_data.get('first_name'):
                user.first_name = fb_data.get('first_name')
            if fb_data.get('last_name'):
                user.last_name = fb_data.get('last_name')
            user.save()

            if name:
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
                    if account.auth_provider != 'facebook':
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

                        # Create user with available information
                        user = User.objects.create(
                            username=account_id,
                            email=email,
                            first_name=fb_data.get('first_name', ''),
                            last_name=fb_data.get('last_name', '')
                        )

                        # Create account
                        account = Account.objects.create(
                            user=user,
                            account_id=account_id,
                            nickname=name or social_id,  # Use social_id as fallback if name not available
                            account_status='verified',
                            auth_provider='facebook',
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
                                nickname=name or social_id,
                                account_status='verified',
                                auth_provider='facebook',
                                social_id=social_id
                            )
                        else:
                            if account.auth_provider is None:
                                # Update the account if auth_provider is None
                                account.auth_provider = 'facebook'
                                account.social_id = social_id
                                account.nickname = name or account.nickname
                                account.account_status = 'verified'
                                account.save()
                            elif account.auth_provider != 'facebook':
                                return Response({
                                    'error': f'This account is already registered with {account.auth_provider or "another provider"}.'
                                }, status=status.HTTP_400_BAD_REQUEST)
                            elif account.social_id != social_id:
                                return Response({
                                    'error': 'This account is already linked to a different Facebook account.'
                                }, status=status.HTTP_400_BAD_REQUEST)
                            else:
                                # Update existing Facebook account information
                                if fb_data.get('first_name'):
                                    user.first_name = fb_data.get('first_name')
                                if fb_data.get('last_name'):
                                    user.last_name = fb_data.get('last_name')
                                user.save()

                                if name:
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
                response = requests.get(picture_url)
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

    except Exception as e:
        logger.error(f"Unexpected error in facebook_auth: {str(e)}")
        return Response({
            'error': 'An unexpected error occurred'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
