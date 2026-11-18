# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

import datetime as dt

from django import template

register = template.Library()


@register.filter
def iso_calendar_week(date: dt.date):
    """Render a date as a ISO calendar week."""
    week = date.isocalendar()

    date_first = dt.date.fromisocalendar(week.year, week.week, 1)
    date_last = dt.date.fromisocalendar(week.year, week.week, 7)

    return f"{week.year}-W{week.week:02d} ({date_first.strftime('%Y-%m-%d')} - {date_last.strftime('%Y-%m-%d')})"
