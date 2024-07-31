from django.contrib import admin
from .models import Book


class BookAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'note')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    list_per_page = 10


# Register your models here.
admin.site.register(Book, BookAdmin)
