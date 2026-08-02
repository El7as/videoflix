from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import django_rq


from .tasks import convert_to_hls_job


class Video(models.Model):
    """
    Represents a video uploaded by a user.

    This model stores:
    - Basic metadata (title, description, category)
    - Thumbnail image
    - Original video file
    - Preferred resolution
    - Creation timestamp

    After saving a new video, a background job is triggered to convert
    the uploaded file into HLS format using FFmpeg.
    """
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    thumbnail_url = models.ImageField(upload_to='thumbnails/')
    file = models.FileField(upload_to='videos/')
    category = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    resolution = models.CharField(max_length=20, choices=[('480p', '480p'), ('720p', '720p'), ('1080p', '1080p'),], default='720p')


    def __str__(self):
        """Return the video title for admin and debugging."""
        return self.title

    class Meta:
        ordering = ['-created_at']



@receiver(post_save, sender=Video)
def enqueue_conversion(sender, instance, created, **kwargs):
    """
    Automatically enqueue an HLS conversion job whenever a new video is created.

    This uses django-rq to push the conversion task into the 'default' queue.
    The worker will then execute FFmpeg to generate HLS playlists and segments.
    """
        
    if created:
        queue = django_rq.get_queue('default')
        queue.enqueue(convert_to_hls_job, instance.file.path, instance.id)
