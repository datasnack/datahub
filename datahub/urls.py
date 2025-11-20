# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

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

import logging
from importlib.util import find_spec

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from .api import api

logger = logging.getLogger(__name__)

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
]

urlpatterns += [
    path("", include("app.urls")),
    path("admin/", admin.site.urls),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(redirect_authenticated_user=True),
    ),
    path("accounts/", include("django.contrib.auth.urls")),
    path("datalayers/", include("datalayers.urls")),
    path("shapes/", include("shapes.urls")),
]

# check if user apps have urls
for app in settings.INSTALLED_USER_APPS:
    try:
        urlpatterns += [path("", include(f"{app}.urls"))]
    except ModuleNotFoundError:
        logger.warning("User app url could not be loaded: %s", app)


if settings.DEBUG and find_spec("debug_toolbar") is not None:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]

# Add django-ninja API URLs last. If they were added before the installed apps loop
# would sometimes lead to strange error messages, as if the API URLs were added twice
urlpatterns += [
    path("api/", api.urls),
]
