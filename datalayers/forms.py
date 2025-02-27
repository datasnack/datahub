from django import forms

from .models import Datalayer, SourceMetadata


class SourceMetadataSelectionForm(forms.Form):
    """From to select meta data from ONE model and copy it to ONE other Data Layer."""

    def __init__(self, *args, datalayer=None, **kwargs) -> None:
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


class SourceMetadataSelectionFromForm(forms.Form):
    """From to select MANY Data Layer and copy ALL metadata from ONE Data Layer."""

    def __init__(self, *args, ids=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if ids:
            self.fields["target_datalayers"].queryset = Datalayer.objects.filter(
                id__in=ids
            )

    source_datalayer = forms.ModelChoiceField(
        queryset=Datalayer.objects.all(), required=True, label="Source Datalayer"
    )

    target_datalayers = forms.ModelMultipleChoiceField(
        queryset=Datalayer.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )

    append_copy_to_new_name = forms.BooleanField(
        required=False,
        initial=False,
        label="Add ' (COPY)' to the end of the name of the copied SourceMetadata",
    )

    delete_existing = forms.BooleanField(
        required=False,
        initial=False,
        label="Delete all existing SourceMetadata in target before copying",
    )
