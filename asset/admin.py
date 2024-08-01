from django.contrib import admin
from .models import Asset, AssetGroup


class AssetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'group', 'balance')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    list_per_page = 10


class AssetGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    list_per_page = 10


# Register your models here.
admin.site.register(Asset, AssetAdmin)
admin.site.register(AssetGroup, AssetGroupAdmin)
