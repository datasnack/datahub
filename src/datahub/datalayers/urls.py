# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from django.urls import path

from . import views

app_name = "datalayers"
urlpatterns = [
    # path("", views.index, name="index"),
    path("", views.DatalayerListView.as_view(), name="datalayer_index"),
    path("<slug:key>/", views.DatalayerDetailView.as_view(), name="datalayer_detail"),
    path("<slug:key>/log", views.DatalayerLogView.as_view(), name="datalayer_log"),
    path(
        "<slug:key>/datacite",
        views.DatalayerDataCiteView.as_view(),
        name="datalayer_datacite",
    ),
    path(
        "tag/<slug:tag_slug>",
        views.DatalayerListView.as_view(),
        name="datalayer_index_tag",
    ),
    path(
        "category/<int:category_id>",
        views.DatalayerListView.as_view(),
        name="datalayer_index_category",
    ),
]
