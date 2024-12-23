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
    path('combined/', views.CombinedListView.as_view(), name='combined-list'),
    path('category/', views.CategoriedRecordView.as_view(), name='categoried-list'),
    path('monthly-data/', views.MonthlyDataView.as_view(), name='monthly-data'),
    path('trend/', views.RecordTrendView.as_view(), name='trend'),

    # New scheduled record endpoints
    path('scheduled/', views.ScheduledRecordList.as_view(), name='scheduled-list'),
    path('scheduled/<int:pk>/', views.ScheduledRecordDetail.as_view(),
         name='scheduled-detail'),
    path('scheduled/<int:pk>/pause/',
         views.ScheduledRecordPause.as_view(), name='scheduled-pause'),
    path('scheduled/<int:pk>/resume/',
         views.ScheduledRecordResume.as_view(), name='scheduled-resume'),
    path('scheduled/<int:pk>/execute/',
         views.ScheduledRecordExecute.as_view(), name='scheduled-execute'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
