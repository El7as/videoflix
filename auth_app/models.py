from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    This model switches authentication from the default `username`
    to `email` as the primary login identifier. It also adds fields
    for account verification and activation tracking.
    """

    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    activated_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        """
        String representation of the user object.
        Returning the email makes it easy to identify users in logs,
        admin panels, and debugging output.
        """
        return self.email
