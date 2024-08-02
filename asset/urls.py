from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

urlpatterns = [
    # Asset urls
    path('', views.AssetList.as_view(), name='asset-list'),
    path('<int:pk>/', views.AssetDetail.as_view()),
    # AssetGroup urls
    path('group-list', views.AssetGroupList.as_view(), name='asset-group-list'),
    path('group-list/<int:pk>/', views.AssetGroupDetail.as_view())
]

urlpatterns = format_suffix_patterns(urlpatterns)
