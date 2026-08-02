from django.urls import path
from .views import VideoListView, VideoManifestView, VideoSegmentView



urlpatterns = [

    # List all videos
    path('video/', VideoListView.as_view(), name='video_list'),

    # HLS master playlist (index.m3u8)
    path('video/<int:movie_id>/<str:resolution>/index.m3u8', VideoManifestView.as_view(), name='video_manifest'),

    # HLS segments (.ts files)
    path('video/<int:movie_id>/<str:resolution>/<str:segment>/', VideoSegmentView.as_view(), name='video_segment'),
]
