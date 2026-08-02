from django.apps import AppConfig


class AuthAppConfig(AppConfig):
    """
    Django application configuration for the authentication app.

    This class allows Django to recognize the app, load signals,
    and perform initialization logic when the project starts.
    """
        
    name = 'auth_app'
