from rest_framework import serializers
from ..models import Video



class VideoSerializer(serializers.ModelSerializer):
    """
    Serializer for the Video model.

    This serializer exposes:
    - Basic metadata (title, description, category)
    - Thumbnail URL
    - Creation timestamp
    - ID for referencing the video

    Note:
    The actual video file and HLS output are not exposed here.
    """

    thumbnail_url = serializers.ImageField(source='thumbnail', use_url=True)
        
    class Meta:
        model = Video
        fields = ['id','created_at', 'title', 'description', 'thumbnail_url','category', ]

