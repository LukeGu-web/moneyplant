from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

urlpatterns = [path('', views.RecordList.as_view()), path(
    '<int:pk>/', views.RecordDetail.as_view())]

urlpatterns = format_suffix_patterns(urlpatterns)
