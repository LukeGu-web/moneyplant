from django.contrib import admin
from .models import Account
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

admin.site.unregister(User)  # Necessary


class AccountInline(admin.TabularInline):
    model = Account


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (AccountInline,)
