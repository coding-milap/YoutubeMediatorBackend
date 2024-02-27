from django.urls import path
from .import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('user-register/',views.user_register,name="user_register"),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('index/',views.index,name="index"),
    path("notifications/",views.notifications,name="notifications"),
    path("send-connection-request/<str:user_email>",views.send_connection_request,name="send-connection-request"),
    path("accept-connection-request/<str:user_email>",views.accept_connection_request,name="accept-connection-request"),
    path('user-profile/',views.user_profile,name='user-profile'),
    path('cancel-request/<str:user_email>',views.cancel_request,name="cancel-request"),
    path('video-upload/',views.VideoView.as_view(),name="video-upload"),
    path('get-creators/',views.connected_users,name="connected-users"),
    path('authorize/<str:user>', views.authorize, name='authorize'),
    path('oauth2callback/', views.oauth2callback, name='oauth2callback'),
    path('video-details/',views.video_details,name="video-details"),
    path('cancel-upload/',views.cancel_upload,name="cancel-upload"),
    # path('youtube-upload/',views.youtube_upload,name="youtube-upload"),
    path('youtube-upload-2/',views.upload_to_youtube,name="youtube-upload-2")
    
]
