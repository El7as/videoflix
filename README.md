Django Video Streaming API (HLS)

A Docker‑based backend for uploading videos, converting them into HLS using FFmpeg, and streaming .m3u8 manifests and .ts segments.
Includes secure cookie‑based JWT authentication, password reset flows, and background processing via django-rq.



Features


Authentication

User registration with password validation
Email activation
Login with HTTP‑Only JWT cookies
Refresh token endpoint
Logout
Password reset (request + confirm)


Video Management

Upload videos
Automatic FFmpeg conversion into: 480p, 720p, 1080p
HLS output: index.m3u8, .ts segments
Streaming endpoints for manifests and segments
Thumbnail upload
Video metadata (title, description, category)


Background Processing

django-rq queue
Redis backend
Worker container running FFmpeg conversion jobs


Docker Architecture

Django backend
Redis
RQ worker
FFmpeg included in the web/worker images
Persistent media volume



Running the Project with Docker


1 Build and start all services

docker-compose up --build

2 Containers

Container	Description
web	Django backend + FFmpeg
redis	Queue backend for django‑rq
worker	Executes FFmpeg conversion jobs
nginx (optional)	Can be added for optimized streaming



Environment Variables

Create a .env file:
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=*
EMAIL_HOST=smtp.example.com
EMAIL_HOST_USER=your@mail.com
EMAIL_HOST_PASSWORD=password



Video Conversion Workflow (FFmpeg)
User uploads a video
Django saves it under media/videos/
post_save signal triggers an RQ job
Worker runs convert_to_hls_job()
FFmpeg generates: index.m3u8, segment0.ts, segment1.ts, …
API serves the manifest and segments



Example Output

media/videos/42/
├── 480p/index.m3u8
├── 480p/segment0.ts
├── 720p/index.m3u8
├── 1080p/index.m3u8



🔗 API Endpoints
Authentication
Method	Endpoint	Description
POST	/auth/register/	Register a new user
POST	/auth/login/	Login (JWT cookies)
POST	/auth/logout/	Logout
POST	/auth/token/refresh/	Refresh access token
POST	/auth/password_reset/	Request password reset
POST	/auth/password_reset_confirm/<uid>/<token>/	Set new password


Videos
Method	Endpoint	Description
GET	/video/	List all videos
GET	/video/<id>/<resolution>/index.m3u8	HLS manifest
GET	/video/<id>/<resolution>/<segment>.ts	HLS segment



JWT via Cookies


Access Token

Short‑lived
Stored in HTTP‑Only cookie

Refresh Token

Longer lifetime
Used to generate new access tokens

Development Commands
Apply migrations
bash
docker-compose exec web python manage.py migrate
Create superuser
bash
docker-compose exec web python manage.py createsuperuser
Run tests
bash
docker-compose exec web python manage.py test


