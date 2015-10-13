__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

from .base_form import BaseForm
from global_app.widgets import CommentInput, TitleField, NestedMultipleChoiceField, NumberInput

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe


class DealWaterForm(BaseForm):

    tg_water_extraction_envisaged = TitleField(required=False, label="", initial=_("Water extraction envisaged"))
    water_extraction_envisaged = forms.ChoiceField(required=False, label=_("Water extraction envisaged"), choices=(
        (10, _("Yes")),
        (20, _("No")),
    ), widget=forms.RadioSelect)
    tg_water_extraction_envisaged_comment = forms.CharField(
        required=False, label=_("Additional comments"), widget=CommentInput
    )

    tg_source_of_water_extraction = TitleField(required=False, label="", initial=_("Source of water extraction"))
    source_of_water_extraction = NestedMultipleChoiceField(
        required=False, label=_("Source of water extraction"),
        choices=(
            (10, _("Groundwater"), None),
            (20, _("Surface water"), (
               (21, _("River")),
               (22, _("Lake")),
            )),
        )
    )
    tg_source_of_water_extraction_comment = forms.CharField(
        required=False, label=_("Additional comments"), widget=CommentInput
    )

    tg_how_much_do_investors_pay = TitleField(
        required=False, label="", initial=_("How much do investors pay for water and the use of water infrastructure?")
    )
    tg_how_much_do_investors_pay_comment = forms.CharField(
        required=False, label=_("Additional comments"), widget=CommentInput
    )

    tg_water_extraction_amount = TitleField(required=False, label="", initial=_("How much water is extracted?"))
    water_extraction_amount = forms.IntegerField(
        required=False, label=_("Water extraction amount"), help_text=mark_safe(_("m&sup3;/year")), widget=NumberInput
    )
    tg_water_extraction_amount_comment = forms.CharField(
        required=False, label=_("Additional comments"), widget=CommentInput
    )