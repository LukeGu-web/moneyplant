from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from user.models import Account
import jwt
import requests
import uuid
import json


@api_view(['POST'])
@permission_classes([AllowAny])
def apple_auth(request):
    try:
        identity_token = request.data.get('identityToken')
        account_id = request.data.get('account_id')  # Optional

        # Fetch Apple's public keys
        keys_response = requests.get('https://appleid.apple.com/auth/keys')
        keys = keys_response.json()

        # Decode the identity token
        try:
            # Note: jwt.decode will verify the signature and expiration
            decoded_token = jwt.decode(
                identity_token,
                options={"verify_signature": True},
                algorithms=['RS256'],
                audience='your.bundle.identifier',  # Replace with your app's bundle ID
                issuer='https://appleid.apple.com',
                jwks_client=jwt.PyJWKClient(
                    'https://appleid.apple.com/auth/keys')
            )
        except jwt.InvalidTokenError as e:
            return Response({
                'error': 'Invalid Apple token'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Extract user info from the token
        # This is the unique user identifier from Apple
        sub = decoded_token.get('sub')
        email = decoded_token.get('email')

        # If email is not provided (user can choose to hide it)
        if not email:
            email = f"{sub}@private.apple.com"

        # Check if user exists
        user = User.objects.filter(email=email).first()

        if not user:
            # Create new user
            username = email
            name = request.data.get('fullName', {})  # From Expo Apple Auth
            first_name = name.get('givenName', '')
            last_name = name.get('familyName', '')

            user = User.objects.create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name
            )

            # Generate account_id if not provided
            if not account_id:
                account_id = f"ACC{uuid.uuid4().hex[:10].upper()}"

            # Create Account
            account = Account.objects.create(
                user=user,
                account_id=account_id,
                nickname=f"{first_name} {
                    last_name}".strip() or email.split('@')[0],
                account_status='verified',
                auth_provider='apple',
                social_id=sub
            )

        else:
            # Get or create account for existing user
            account, created = Account.objects.get_or_create(
                user=user,
                defaults={
                    'account_id': account_id or f"ACC{uuid.uuid4().hex[:10].upper()}",
                    'nickname': user.get_full_name() or email.split('@')[0],
                    'account_status': 'verified',
                    'auth_provider': 'apple',
                    'social_id': sub
                }
            )

            # Update existing account if needed
            if not created:
                account.auth_provider = 'apple'
                account.social_id = sub
                account.account_status = 'verified'
                account.save()

        # Get or create token
        token, _ = Token.objects.get_or_create(user=user)

        # Return response in the same structure as Facebook login
        return Response({
            'id': account.id,
            'account_id': account.account_id,
            'avatar': None,  # Apple doesn't provide profile pictures
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
