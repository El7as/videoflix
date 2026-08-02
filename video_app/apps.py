from django.apps import AppConfig


class VideoAppConfig(AppConfig):
    """
    Django application configuration for the video app.

    This class allows Django to:
    - Recognize the application
    - Load signals
    - Perform initialization logic when the project starts
    """
        
    name = 'video_app'
