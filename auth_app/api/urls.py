from django.urls import path


from .views import RegisterView, ActivateAccountView, LoginView, LogoutView, RefreshTokenView, PasswordResetView, PasswordConfirmView



urlpatterns = [
    
    # User registration
    path('register/', RegisterView.as_view(), name='register'),

    # Email activation link
    path('activate/<uidb64>/<token>/', ActivateAccountView.as_view(), name='activate'),

    # Authentication endpoints
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # JWT refresh endpoint (cookie‑based)
    path('token/refresh/', RefreshTokenView.as_view(), name='token_refresh'),

    # Password reset (request + confirm)
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_confirm/<uidb64>/<token>/', PasswordConfirmView.as_view(), name='password_confirm'),
]
