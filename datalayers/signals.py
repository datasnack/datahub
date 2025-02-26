from django.db.models import Max
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import SourceMetadata


@receiver(pre_save, sender=SourceMetadata)
def set_position(sender, instance, **kwargs):
    """
    Check if the position for a SourceMetadata is 0, and if so determine the current maximum and append the new source.
    This is realized with a signal instead of overwriting the SourceMetadata.save() method
    because the save() method is not called in context of the nested Admin forms.
    """
    if instance.position == 0 and instance.datalayer:
        last_position = (
            instance.datalayer.sources.aggregate(Max("position"))["position__max"] or 0
        )
        instance.position = last_position + 10
