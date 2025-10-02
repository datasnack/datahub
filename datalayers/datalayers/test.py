# SPDX-FileCopyrightText: 2025 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from datalayers.datasources.copernicus_layer import CopernicusLayer


class Test(CopernicusLayer):
    def __init__(self) -> None:
        super().__init__()

        self.area_of_interest = [
            "ENF_closed",
            "EBF_closed",
            "DNF_closed",
            "DBF_closed",
            "mixed_closed",
            "unknown_closed",
            "ENF_open",
            "EBF_open",
            "DNF_open",
            "DBF_open",
            "mixed_open",
            "unknown_open",
        ]
