from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

urlpatterns = [
    path('all/', views.all_records_view),
    path('tax-only/', views.tax_only_records_view),
    path('record/', views.RecordList.as_view()),
    path('record/<int:pk>/', views.RecordDetail.as_view()),
    path('transfer/', views.TransferList.as_view()),
    path('transfer/<int:pk>/', views.TransferDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
