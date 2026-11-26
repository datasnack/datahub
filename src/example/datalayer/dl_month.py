from datahub.datalayers.datasources.base_layer import (
    BaseLayer,
    LayerTimeResolution,
    LayerValueType,
)


class DlMonth(BaseLayer):
    def __init__(self) -> None:
        super().__init__()
        self.value_type = LayerValueType.FLOAT
        self.time_col = LayerTimeResolution.DAY

    def download(self):
        raise NotImplementedError

    def process(self, shapes):
        raise NotImplementedError
