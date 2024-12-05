from django.db import models

# Create your models here.
class ShapeDataLayerYearStats(models.Model):
    shape_id = models.IntegerField(null=False)
    data_layer = models.CharField(max_length=255, null=False)
    year = models.IntegerField(null=False)
    value = models.FloatField()

    class Meta:
        unique_together = ('shape_id', 'data_layer', 'year')
        indexes = [
            models.Index(fields=['shape_id', 'data_layer', 'year']),
        ]

    def __str__(self):
        return f"{self.shape_id} - {self.data_layer} - {self.year}: {self.value}"
