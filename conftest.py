# SPDX-FileCopyrightText: 2026 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

import pytest

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import GEOSGeometry

from datalayers.models import Datalayer
from shapes.models import Shape, Type

User = get_user_model()


# --- User fixtures ---


@pytest.fixture
def user(db):
    return User.objects.create_user(username="regular", password="pass")  # noqa: S106


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(username="staff", password="pass", is_staff=True)  # noqa: S106


@pytest.fixture
def super_user(db):
    return User.objects.create_user(
        username="super",
        password="pass",  # noqa: S106
        is_superuser=True,
    )


# --- Shape fixtures ---


# We use transactional_db here (which should cascade to further `db` usages?). We need
# to persist the models *and* the data (created by dl.process() Datalayer fixtures) in the
# same transaction so they are available to the tests.
@pytest.fixture
def type_country(transactional_db):
    return Type.objects.create(name="Country", key="country")


@pytest.fixture
def type_region(transactional_db):
    return Type.objects.create(name="Region", key="region")


@pytest.fixture
def shape_country(type_country):
    geometry_string = """
    {
    "type": "Polygon",
    "coordinates": [
        [
        [10.0, 50.0],
        [11.0, 50.0],
        [11.0, 51.0],
        [10.0, 51.0],
        [10.0, 50.0]
        ]
    ]
    }
    """

    geom = GEOSGeometry(geometry_string, srid=4326)

    return Shape.objects.create(
        name="Test Country", key="CC01", geometry=geom, type=type_country
    )


@pytest.fixture
def shape_region_upper(type_region):
    # upper half of the country polygon
    geometry_string = """
    {
    "type": "Polygon",
    "coordinates": [
        [
        [10.0, 50.5],
        [11.0, 50.5],
        [11.0, 51],
        [10.0, 51],
        [10.0, 50.5]
        ]
    ]
    }
    """

    geom = GEOSGeometry(geometry_string, srid=4326)

    return Shape.objects.create(
        name="Upper region", key="CC011", geometry=geom, type=type_region
    )


@pytest.fixture
def shape_region_lower(type_region):
    # lower half of the country polygon
    geometry_string = """
    {
    "type": "Polygon",
    "coordinates": [
        [
        [10.0, 50.0],
        [11.0, 50.0],
        [11.0, 50.5],
        [10.0, 50.5],
        [10.0, 50.0]
        ]
    ]
    }
    """

    geom = GEOSGeometry(geometry_string, srid=4326)

    return Shape.objects.create(
        name="Lower region", key="CC012", geometry=geom, type=type_region
    )


# --- Data Layer fixtures ---


@pytest.fixture
def dl_listed(shape_country, shape_region_upper, shape_region_lower):
    dl = Datalayer.objects.create(
        key="test_csv",
        name="Data Layer 1",
        visibility=Datalayer.Visibility.LISTED,
        data_access=True,
    )

    dl.process([shape_country, shape_region_upper, shape_region_lower])
    dl.get_class().save()

    return dl


@pytest.fixture
def dl_listed_no_data(shape_country):
    dl = Datalayer.objects.create(
        key="test_csv3",
        name="Data Layer 3",
        visibility=Datalayer.Visibility.LISTED,
        data_access=False,
    )

    dl.process([shape_country])
    dl.get_class().save()

    return dl


@pytest.fixture
def dl_private(shape_country):
    dl = Datalayer.objects.create(
        key="test_csv2",
        name="Data Layer 2",
        visibility=Datalayer.Visibility.PRIVATE,
        data_access=True,
    )

    dl.process([shape_country])
    dl.get_class().save()

    return dl


# --- Authenticated client fixtures ---


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    client.force_login(admin_user)
    return client
