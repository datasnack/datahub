# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from .models import Category


def add_navigation(request):
    categories = Category.objects.order_by("position", "name")
    return {"nav_datalayer_categories": categories}
