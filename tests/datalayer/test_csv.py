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
        for shape in shapes:
            for i in range(1, 20 + 1):
                self.add_value(shape, 2000 + i, i)
