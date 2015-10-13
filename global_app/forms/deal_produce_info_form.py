
__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

from .base_form import BaseForm

from global_app.widgets import TitleField, CommentInput, NumberInput
from landmatrix.models.animal import Animal
from landmatrix.models.country import Country
from landmatrix.models.crop import Crop
from landmatrix.models.mineral import Mineral

from django import forms
from django.utils.translation import ugettext_lazy as _


class DealProduceInfoForm(BaseForm):

    # Detailed crop, animal and mineral information
    tg_crop_animal_mineral = TitleField(required=False, label="", initial=_("Detailed crop, animal and mineral information"))
    crops = forms.ModelMultipleChoiceField(required=False, label=_("Crops"), queryset=Crop.objects.all(), widget=forms.CheckboxSelectMultiple)
    animals = forms.ModelMultipleChoiceField(required=False, label=_("Animals"), queryset=Animal.objects.all(), widget=forms.CheckboxSelectMultiple)
    minerals = forms.ModelMultipleChoiceField(required=False, label=_("Minerals"), queryset=Mineral.objects.all(), widget=forms.CheckboxSelectMultiple)

    # Use of produce
    tg_use_of_produce = TitleField(required=False, label="", initial=_("Use of produce"))
    has_domestic_use = forms.BooleanField(required=False, label=_("Has domestic use"))
    domestic_use = forms.IntegerField(required=False, label=_("Domestic use"), help_text=_("%"), widget=NumberInput)
    has_export = forms.BooleanField(required=False, label=_("Has export"))
    export = forms.IntegerField(required=False, label=_("Export"), help_text=_("%"), widget=NumberInput)
    export_country1 = forms.ModelChoiceField(required=False, label=_("Country 1"), queryset=Country.objects.all().order_by("name"))
    export_country1_ratio = forms.IntegerField(required=False, label=_("Country 1 ratio"), help_text=_("%"), widget=NumberInput)
    export_country2 = forms.ModelChoiceField(required=False, label=_("Country 2"), queryset=Country.objects.all().order_by("name"))
    export_country2_ratio = forms.IntegerField(required=False, label=_("Country 2 ratio"), help_text=_("%"), widget=NumberInput)
    export_country3 = forms.ModelChoiceField(required=False, label=_("Country 3"), queryset=Country.objects.all().order_by("name"))
    export_country3_ratio = forms.IntegerField(required=False, label=_("Country 3 ratio"), help_text=_("%"), widget=NumberInput)
    tg_use_of_produce_comment = forms.CharField(required=False, label=_("Additional comments"), widget=CommentInput)

    # In-country processing of produce
    tg_in_country_processing = TitleField(required=False, label="", initial=_("In country processing of produce"))
    in_country_processing = forms.ChoiceField(required=False, label=_("In country processing of produce"), choices=(
        (10, _("Yes")),
        (20, _("No")),
    ), widget=forms.RadioSelect)
    tg_in_country_processing_comment = forms.CharField(required=False, label=_("Additional comments"), widget=CommentInput)


class PublicViewDealProduceInfoForm(DealProduceInfoForm):

    class Meta:
        fields = (
            "tg_crop_animal_mineral", "crops",
        )
        readonly_fields = (
            "tg_crop_animal_mineral", "crops",
        )