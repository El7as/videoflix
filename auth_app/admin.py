from django.contrib import admin

from .models import User

"""
Register your custom User model in the Django admin interface.
This allows administrators to view, edit, and manage users directly
from the Django admin dashboard
"""

admin.site.register(User)