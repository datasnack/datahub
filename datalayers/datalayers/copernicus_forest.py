from datalayers.datasources.copernicus_layer import CopernicusLayer

class CopernicusForest(CopernicusLayer):

    def __init__(self):
        super().__init__()

        self.area_of_interest = [
            'ENF_closed',
            'EBF_closed',
            'DNF_closed',
            'DBF_closed',
            'mixed_closed',
            'unknown_closed',

            'ENF_open',
            'EBF_open',
            'DNF_open',
            'DBF_open',
            'mixed_open',
            'unknown_open',
        ]
