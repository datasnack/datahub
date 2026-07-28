# SPDX-FileCopyrightText: 2026 Jonathan Ströbele <mail@jonathanstroebele.de>
#
# SPDX-License-Identifier: AGPL-3.0-only

from datalayers.datasources.base_layer import (
    BaseLayer,
    LayerTimeResolution,
    LayerValueType,
)
from shapes.models import Shape


class TestCsv(BaseLayer):
    __test__ = False

    def __init__(self) -> None:
        super().__init__()
        self.time_col = LayerTimeResolution.YEAR
        self.value_type = LayerValueType.INTEGER

    def download(self):
        pass

    def process(self, shapes: list[Shape]):
        data = {
            "CC01": [5, 2, 0, 3, 5, 10, 2, 1],
            "CC011": [2, 0, 0, 2, 5, 7, 1, 1],
            "CC012": [3, 2, 0, 1, 0, 3, 1, 0],
        }

        for shape in shapes:
            shape_data = data.get(shape.key)

            for idx, x in enumerate(shape_data):
                self.add_value(shape, 2000 + idx, x)
