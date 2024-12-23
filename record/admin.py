from django.contrib import admin
from .models import Record, Transfer


class RecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'book', 'asset', 'amount', 'user')
    list_display_links = ('id',)
    search_fields = ('book__user__username', 'asset__name', 'amount')
    list_filter = ('book__user',) 

    def user(self, obj):
        return obj.book.user if obj.book else None

    user.short_description = "User"


class TransferAdmin(admin.ModelAdmin):
    list_display = ('id', 'book', 'from_asset', 'to_asset', 'amount', 'user')
    list_display_links = ('id',)
    search_fields = ('book__user__username', 'from_asset__name', 'to_asset__name', 'amount')
    list_filter = ('book__user',)  

    def user(self, obj):
        return obj.book.user if obj.book else None

    user.short_description = "User"

# Register your models here.
admin.site.register(Record, RecordAdmin)

admin.site.register(Transfer, TransferAdmin)
