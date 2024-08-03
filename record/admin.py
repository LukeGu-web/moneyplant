from django.contrib import admin
from .models import Record, Transfer


class RecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'book', 'amount')
    list_display_links = ('id',)


# Register your models here.
admin.site.register(Record, RecordAdmin)

admin.site.register(Transfer, RecordAdmin)
