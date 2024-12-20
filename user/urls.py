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
    # path("logout/", views.logout_user, name="logout"),
    path('details/', views.user_details_view),
    path('<int:pk>/', views.AccountDetail.as_view()),
    path("login/", obtain_auth_token, name="login"),
    path('auth/apple/', views.apple_auth, name='apple_auth'),
    path('auth/facebook/', views.facebook_auth, name='facebook_auth'),
    path('auth/google/', views.google_auth, name='google_auth'),
    path("device-register/", views.device_register_view, name="device_register"),
    path("send-verify-email/", views.send_verification_email,
         name="send_verify_email"),
    path('verify-email/<uidb64>/<token>/',
         views.VerifyEmail.as_view(), name='verify_email'),
    path('register-push-token/', views.register_push_token,
         name='register_push_token'),
    path("tax-return/", views.tax_return_view),
    path("fill-pdf/", views.fill_pdf_view),
]
