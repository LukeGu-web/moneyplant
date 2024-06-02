from django.urls import path
from . import views

urlpatterns = [path('', views.getRecords), path(
    'test', views.second), path('<id>', views.index)]
