from django.contrib import admin

from .models import Video


"""
Register the Video model so it appears in the Django admin interface.
This allows administrators to view, edit, and manage uploaded videos.
"""
admin.site.register(Video)
