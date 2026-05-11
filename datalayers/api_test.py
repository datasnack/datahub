# SPDX-FileCopyrightText: 2026 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from urllib.parse import urlencode

import pytest

from django.urls import reverse


class TestMyModelView:
    @pytest.fixture(autouse=True)
    def require_no_login(self, settings):
        settings.DATAHUB_LOGIN_REQUIRED = False

    #
    # Anonymous user
    #
    def test_anonymous_user_public_dl(self, client, dl_listed):
        url = reverse("api-1.0.0:data", args=[])
        response = client.get(
            f"{url}?{urlencode({'datalayer_key': dl_listed.key}, doseq=True)}"
        )

        assert response.status_code == 200

    def test_anonymous_user_unknown_dl(self, client, db):
        url = reverse("api-1.0.0:data", args=[])
        response = client.get(
            f"{url}?{urlencode({'datalayer_key': 'does_not_exist'}, doseq=True)}"
        )

        assert response.status_code == 404

    def test_anonymous_user_private_dl(self, client, dl_private):
        url = reverse("api-1.0.0:data", args=[])
        response = client.get(
            f"{url}?{urlencode({'datalayer_key': dl_private.key}, doseq=True)}"
        )

        assert response.status_code == 404

    def test_anonymous_user_public_nodata_dl(self, client, dl_listed_no_data):
        url = reverse("api-1.0.0:data", args=[])
        response = client.get(
            f"{url}?{urlencode({'datalayer_key': dl_listed_no_data.key}, doseq=True)}"
        )

        assert response.status_code == 403

    #
    # Authenticated user, no staff or superuser
    #
    def test_user_public_dl(self, client, user, dl_listed):
        client.force_login(user)

        url = reverse("api-1.0.0:data", args=[])
        response = client.get(
            f"{url}?{urlencode({'datalayer_key': dl_listed.key}, doseq=True)}"
        )

        assert response.status_code == 200

    def test_user_private_dl(self, client, user, dl_private):
        client.force_login(user)

        url = reverse("api-1.0.0:data", args=[])
        response = client.get(
            f"{url}?{urlencode({'datalayer_key': dl_private.key}, doseq=True)}"
        )

        assert response.status_code == 404

    #
    # Staff user
    #
    def test_staff_user_private_dl(self, client, staff_user, dl_private):
        client.force_login(staff_user)

        url = reverse("api-1.0.0:data", args=[])
        response = client.get(
            f"{url}?{urlencode({'datalayer_key': dl_private.key}, doseq=True)}"
        )

        assert response.status_code == 404

    #
    # Super user
    #
    def test_super_user_private_dl(self, client, super_user, dl_private):
        client.force_login(super_user)

        url = reverse("api-1.0.0:data", args=[])
        response = client.get(
            f"{url}?{urlencode({'datalayer_key': dl_private.key}, doseq=True)}"
        )

        assert response.status_code == 200
