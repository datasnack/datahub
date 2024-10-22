"""
URL configuration for datahub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/

Examples
--------
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))

"""

from importlib.util import find_spec

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
]

urlpatterns += [
    path("", include("app.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/login/", auth_views.LoginView.as_view()),
    path("datalayers/", include("datalayers.urls")),
    path("shapes/", include("shapes.urls")),
    path("api/", include("shapes.api.urls")),
    path("api/", include("datalayers.api.urls")),
]

# check if user apps have urls
for app in settings.INSTALLED_USER_APPS:
    try:
        urlpatterns += [path("", include(f"{app}.urls"))]
    except ModuleNotFoundError:
        # todo: error logging
        pass


if settings.DEBUG and find_spec("debug_toolbar") is not None:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
