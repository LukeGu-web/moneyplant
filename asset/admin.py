from django.contrib import admin
from .models import Asset, AssetGroup


class AssetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'group', 'balance', 'book', 'user')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'group__book__name', 'group__book__user__name')
    list_per_page = 10

    def book(self, obj):
        return obj.group.book.name if obj.group and obj.group.book else None

    def user(self, obj):
        return obj.group.book.user if obj.group and obj.group.book else None

    book.short_description = "Book"
    user.short_description = "User"


class AssetGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'book')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'book__name', 'book__user__name')
    list_per_page = 10


# Register your models here.
admin.site.register(Asset, AssetAdmin)
admin.site.register(AssetGroup, AssetGroupAdmin)
