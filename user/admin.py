from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_id', 'account_status', 'auth_provider')
    search_fields = ('user__email', 'account_id', 'nickname')
    list_filter = ('account_status', 'auth_provider')

    def get_deleted_objects(self, objs, request):
        """
        Hook to customize the deletion preview
        """
        deletable_objects, model_count, perms_needed, protected = super(
        ).get_deleted_objects(objs, request)
        # Add User to the list of objects that will be deleted
        for obj in objs:
            if obj.user:
                deletable_objects.append(obj.user)
                if 'Users' in model_count:
                    model_count['Users'] += 1
                else:
                    model_count['Users'] = 1
        return deletable_objects, model_count, perms_needed, protected
