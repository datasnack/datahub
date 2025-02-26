from django import forms

from .models import Datalayer, SourceMetadata


class SourceMetadataSelectionForm(forms.Form):
    def __init__(self, *args, datalayer=None, **kwargs):
        super().__init__(*args, **kwargs)
        if datalayer:
            self.fields["source_metadata"].queryset = SourceMetadata.objects.filter(
                datalayer=datalayer
            )

    source_metadata = forms.ModelMultipleChoiceField(
        queryset=SourceMetadata.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )

    append_copy_to_new_name = forms.BooleanField(
        required=False,
        initial=False,
        label="Add ' (COPY)' to the end of the name of the copied SourceMetadata",
    )

    new_datalayer = forms.ModelChoiceField(
        queryset=Datalayer.objects.all(), required=True, label="Target Datalayer"
    )
    delete_existing = forms.BooleanField(
        required=False,
        initial=False,
        label="Delete all existing SourceMetadata in target before copying",
    )
