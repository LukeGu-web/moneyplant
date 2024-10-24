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
from jwt.algorithms import RSAAlgorithm


@api_view(['POST'])
@permission_classes([AllowAny])
def apple_auth(request):
    try:
        # Get the identity token from request
        # We're using accessToken in the request
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
        sub = decoded_token.get('sub')  # Apple user ID
        email = decoded_token.get('email')
        email_verified = decoded_token.get('email_verified', False)

        if not email:
            email = f"{sub}@private.apple.com"

        # Check if user exists
        user = User.objects.filter(email=email).first()

        if not user:
            # Create new user
            username = email
            user = User.objects.create(
                username=username,
                email=email
            )

            # Generate account_id if not provided
            if not account_id:
                account_id = f"ACC{uuid.uuid4().hex[:10].upper()}"

            # Create Account
            account = Account.objects.create(
                user=user,
                account_id=account_id,
                nickname=email.split('@')[0],
                account_status='verified' if email_verified else 'pending',
                auth_provider='apple',
                social_id=sub
            )

        else:
            # Get or create account for existing user
            account, created = Account.objects.get_or_create(
                user=user,
                defaults={
                    'account_id': account_id or f"ACC{uuid.uuid4().hex[:10].upper()}",
                    'nickname': email.split('@')[0],
                    'account_status': 'verified' if email_verified else 'pending',
                    'auth_provider': 'apple',
                    'social_id': sub
                }
            )

            if not created:
                account.auth_provider = 'apple'
                account.social_id = sub
                account.account_status = 'verified' if email_verified else 'pending'
                account.save()

        # Get or create token
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'id': account.id,
            'account_id': account.account_id,
            'avatar': None,
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
