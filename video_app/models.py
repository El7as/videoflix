from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import django_rq


from .tasks import convert_to_hls_job


class Video(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    thumbnail_url = models.ImageField(upload_to='thumbnails/')
    file = models.FileField(upload_to='videos/')
    category = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    resolution = models.CharField(max_length=20, choices=[('480p', '480p'), ('720p', '720p'), ('1080p', '1080p'),], default='720p')


    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']



@receiver(post_save, sender=Video)
def enqueue_conversion(sender, instance, created, **kwargs):
    if created:
        queue = django_rq.get_queue('default')
        queue.enqueue(convert_to_hls_job, instance.file.path, instance.id)
