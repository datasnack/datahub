from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

# Update translation keys in admin
admin.site.site_header = _('Data Hub administration')
admin.site.site_title  = _('Data Hub admin')


# Register your models here.
admin.site.register(User, UserAdmin)

class MyAdminSite(admin.AdminSite):
    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        app_list += [
            {
                "name": "My Custom App",
                "app_label": "my_test_app",
                # "app_url": "/admin/test_view",
                "models": [
                    {
                        "name": "tcptraceroute",
                        "object_name": "tcptraceroute",
                        "admin_url": "/admin/test_view",
                        "view_only": True,
                    }
                ],
            }
        ]
        return app_list
