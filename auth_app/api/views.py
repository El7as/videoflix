from django.utils import timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from django.conf import settings

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


from .serializers import RegisterSerializer, PasswordResetConfirmSerializer



User = get_user_model()



class RegisterView(generics.CreateAPIView):
    """
    API endpoint for user registration.

    This view:
    - Validates incoming registration data
    - Creates a new user
    - Generates an activation token + UID
    - Sends an activation email with a secure link
    - Returns basic user info and the token
    """

    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        """
        Handle POST requests to register a new user.

        Steps:
        1. Validate the incoming data using the serializer.
        2. Save the new user instance.
        3. Generate a UID and token for account activation.
        4. Build an activation link.
        5. Send an activation email.
        6. Return a response containing user info and token.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # activation_link = request.build_absolute_uri(f"/api/activate/{uidb64}/{token}/")
        activation_link = f'{settings.FRONTEND_URL}/pages/auth/activate.html?uid={uidb64}&token={token}'

        send_mail(
            subject='Activate your account',
            message=f'Hi {user.email}, please activate your account: \n{activation_link}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,)

        return Response({'user': {'id': user.id, 'email': user.email}, 'token': token}, status=status.HTTP_201_CREATED)



class ActivateAccountView(generics.GenericAPIView):
    """
    Handles account activation via a GET request.

    The activation link contains:
    - uidb64: Base64-encoded user ID
    - token: A time-sensitive activation token

    When the user clicks the link:
    - The UID is decoded
    - The user is retrieved
    - The token is validated
    - The account is activated if valid
    """

    def get(self, request, uidb64, token):
        """
        Process the activation link.

        Steps:
        1. Decode the UID from base64.
        2. Retrieve the corresponding user.
        3. Validate the token.
        4. Activate the user if valid.
        """

        try:
            
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.is_verified = True
            user.save()
            return Response({'message': 'Account successfully activated.'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Activation failed.'}, status=status.HTTP_400_BAD_REQUEST)




class LoginView(APIView):
    """
    Handles user login using email + password.

    This view:
    - Validates login input
    - Authenticates the user
    - Checks activation status
    - Generates JWT access + refresh tokens
    - Stores both tokens in HTTP-only cookies
    """

    def post(self, request, *args, **kwargs):
        """
        Process login requests.

        Steps:
        1. Extract email and password.
        2. Validate input.
        3. Authenticate user.
        4. Check if account is activated.
        5. Generate JWT tokens.
        6. Set tokens in secure cookies.
        7. Return user info.
        """
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:return Response({'detail': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=email, password=password)

        if user is None: return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:return Response({'detail': 'Account is not activated.'},status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        response = Response({'detail': 'Login successful', 'user': {'id': user.id,'username': user.email, },},status=status.HTTP_200_OK)

        response.set_cookie('access_token', access_token, httponly=True, secure=False, samesite='Lax',)
        response.set_cookie('refresh_token', str(refresh), httponly=True, secure=False, samesite='Lax',)

        return response



class LogoutView(APIView):
    """
    Handles user logout by:
    - Reading the refresh token from cookies
    - Blacklisting the refresh token (invalidating it)
    - Optionally updating the user's last logout timestamp
    - Clearing authentication cookies
    """


    def post(self, request, *args, **kwargs):
        """
        Process logout requests.

        Steps:
        1. Retrieve refresh token from cookies.
        2. Validate and blacklist the token.
        3. Update user's logout timestamp (optional).
        4. Delete JWT cookies.
        5. Return confirmation response.
        """
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response({'detail': 'Refresh token missing.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({'detail': 'Invalid refresh token.'}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.is_authenticated:
            request.user.activated_at = timezone.now()
            request.user.save()

        response = Response({'detail': 'Logout successful! All tokens will be deleted. Refresh token is now invalid.'}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response


class RefreshTokenView(APIView):
    """
    Provides a new access token using the refresh token stored in cookies.

    This view:
    - Reads the refresh token from the user's cookies
    - Validates the refresh token
    - Generates a new access token
    - Stores the new access token in an HTTP-only cookie
    """

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response({'detail': 'Refresh token missing.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)
        except TokenError:
            return Response({'detail': 'Invalid refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)

        response = Response({'detail': 'Token refreshed', 'access': new_access_token,}, status=status.HTTP_200_OK)
        response.set_cookie('access_token', new_access_token, httponly=True, secure=False, samesite='Lax',)
        return response




class PasswordResetView(APIView):
    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to refresh the access token.

        Steps:
        1. Retrieve refresh token from cookies.
        2. Validate the refresh token.
        3. Generate a new access token.
        4. Set the new access token in a secure cookie.
        5. Return the new token in the response body.
        """
        email = request.data.get('email')

        if not email:
            return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'If the email exists, a reset link has been sent.'}, status=status.HTTP_200_OK)

        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        # reset_link = request.build_absolute_uri(f'/api/password_reset_confirm/{uidb64}/{token}/')
        reset_link =(f'{settings.FRONTEND_URL}/pages/auth/confirm_password.html?uid={uidb64}&token={token}')

        send_mail(subject='Reset your password',
            message=f'Hi {user.email}, click the link to reset your password: {reset_link}',
            from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[user.email],)

        return Response({'detail': 'An email has been sent to reset your password.'}, status=status.HTTP_200_OK)



class PasswordConfirmView(APIView):
    """
    Handles password reset confirmation.

    This view is triggered when the user clicks the password reset link
    sent to their email. The link contains:
    - uidb64: Base64-encoded user ID
    - token: A time-sensitive password reset token

    The view:
    - Validates the UID and token
    - Validates the new password via serializer
    - Updates the user's password
    """


    def post(self, request, uidb64, token, *args, **kwargs):
        """
        Process the password reset confirmation.

        Steps:
        1. Decode UID from base64.
        2. Retrieve the user.
        3. Validate the token.
        4. Validate the new password.
        5. Save the new password.
        """
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({'detail': 'Invalid link.'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_password = request.data.get('new_password')
        user.set_password(new_password)
        user.save()

        return Response({'detail': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
