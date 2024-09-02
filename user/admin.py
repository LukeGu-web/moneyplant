from django.contrib import admin
from .models import Account
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User


class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'account_status', 'created_date')
    list_display_links = ('id', 'user')


admin.site.register(Account, AccountAdmin)
