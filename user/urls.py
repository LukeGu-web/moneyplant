from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from . import views
# from rest_framework_simplejwt.views import (
#     TokenObtainPairView,
#     TokenRefreshView,
# )

urlpatterns = [
    # path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path("login/", obtain_auth_token, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("device-register/", views.device_register_view, name="device-register"),
    path("register/", views.user_register_view, name="register"),
    path('<int:pk>/', views.UserDetail.as_view()),
]
