from django.urls import path
from .views import VideoListView, VideoManifestView, VideoSegmentView



urlpatterns = [
    path('video/', VideoListView.as_view(), name='video_list'),
    path('video/<int:movie_id>/<str:resolution>/index.m3u8', VideoManifestView.as_view(), name='video_manifest'),
    path('video/<int:movie_id>/<str:resolution>/<str:segment>/', VideoSegmentView.as_view(), name='video_segment'),
]
