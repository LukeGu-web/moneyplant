from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from user.models import Account
from user.utils import Util
from book.serializers import BookSerializer
import requests
import uuid
import base64


@api_view(['POST'])
@permission_classes([AllowAny])
def facebook_auth(request):
    try:
        access_token = request.data.get('accessToken')
        account_id = request.data.get('account_id')

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

        # Check if a user exists with the same email but different provider
        user_with_same_email = User.objects.filter(email=email).first()
        if user_with_same_email:
            account = Account.objects.filter(user=user_with_same_email).first()
            if account and account.auth_provider != 'facebook':
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
                email=email,
                first_name=fb_data.get('first_name', ''),
                last_name=fb_data.get('last_name', '')
            )

            # Create a new Account associated with Facebook
            account = Account.objects.create(
                user=user,
                account_id=account_id,
                nickname=name,
                account_status='verified',
                auth_provider='facebook',
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
                    auth_provider='facebook',
                    social_id=social_id
                )
            elif account.auth_provider != 'facebook':
                # User exists with different auth provider
                return Response({
                    'error': f'This account is already registered with {account.auth_provider}.'
                }, status=status.HTTP_400_BAD_REQUEST)
            elif account.social_id != social_id:
                # Different Facebook account trying to use same account_id
                return Response({
                    'error': 'This account is already linked to a different Facebook account.'
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Update existing Facebook account information
                user.first_name = fb_data.get('first_name', '')
                user.last_name = fb_data.get('last_name', '')
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

        response_data = {
            'id': account.id,
            'account_id': account.account_id,
            'avatar': base64.b64encode(account.avatar).decode('utf-8') if account.avatar else None,
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
