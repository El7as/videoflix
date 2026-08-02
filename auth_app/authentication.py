from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication class that allows JWT tokens
    to be read from HTTP-only cookies instead of (or in addition to)
    the Authorization header.

    This is useful when implementing secure, cookie-based authentication
    for SPAs or mobile clients that do not store tokens in localStorage.
    """

    def authenticate(self, request):
        """
        Attempt to authenticate the user using either:
        1. The Authorization header (default behavior), or
        2. The 'access_token' cookie if no header is present.

        Returns:
            (user, validated_token) if authentication succeeds,
            None if no valid token is found.
        """

        header = self.get_header(request)
        if header is None:
            raw_token = request.COOKIES.get('access_token')
        else:
            raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
