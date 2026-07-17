import os

from django.conf import settings
from django.http import HttpResponse, Http404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


from ..models import Video
from .serializers import VideoSerializer



class VideoListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        videos = Video.objects.all().order_by('-created_at')
        serializer = VideoSerializer(videos, many=True)
        return Response(serializer.data)



class VideoManifestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        try:
            video = Video.objects.get(id=movie_id)
        except Video.DoesNotExist:
            raise Http404("Video not found")

        manifest_path = os.path.join(settings.MEDIA_ROOT, 'videos', str(movie_id), resolution, 'index.m3u8')

        if not os.path.exists(manifest_path):
            raise Http404("Manifest not found")

        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_content = f.read()

        return HttpResponse(manifest_content, content_type='application/vnd.apple.mpegurl')



class VideoSegmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        try:
            video = Video.objects.get(id=movie_id)
        except Video.DoesNotExist:
            raise Http404("Video not found")

        segment_path = os.path.join(settings.MEDIA_ROOT, 'videos', str(movie_id), resolution, segment)

        if not os.path.exists(segment_path):
            raise Http404("Segment not found")


        def file_iterator(path, chunk_size=8192):
            with open(path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

        return HttpResponse(file_iterator(segment_path), content_type='video/MP2T')
