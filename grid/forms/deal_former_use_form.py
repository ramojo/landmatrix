from grid.forms.base_form import BaseForm
from grid.widgets import TitleField, CommentInput

from django import forms
from django.utils.translation import ugettext_lazy as _

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


class DealFormerUseForm(BaseForm):

    form_title = _('Former use')

    tg_land_owner = TitleField(
        required=False, label="", initial=_("Former land owner (not by constitution)")
    )
    land_owner = forms.MultipleChoiceField(
        required=False, label=_("Former land owner"), choices=(
            (10, _("State")),
            (20, _("Private (smallholders)")),
            (30, _("Private (large-scale)")),
            (40, _("Community")),
            (50, _("Other")),
        ), widget=forms.CheckboxSelectMultiple
    )
    tg_land_owner_comment = forms.CharField(
        required=False, label=_("Additional comments"), widget=CommentInput
    )

    tg_land_use = TitleField(
        required=False, label="", initial=_("Former land use")
    )
    land_use = forms.MultipleChoiceField(
        required=False, label=_("Former land use"), choices=(
            (10, _("Commercial (large-scale) agriculture")),
            (20, _("Smallholder agriculture")),
            (30, _("Shifting cultivation")),
            (40, _("Pastoralism")),
            (50, _("Hunting/Gathering")),
            (60, _("Forestry")),
            (70, _("Conservation")),
            (80, _("Other")),
        ), widget=forms.CheckboxSelectMultiple
    )
    tg_land_use_comment = forms.CharField(
        required=False, label=_("Additional comments"), widget=CommentInput
    )

    tg_land_cover = TitleField(
        required=False, label="", initial=_("Former land cover")
    )
    land_cover = forms.MultipleChoiceField(
        required=False, label=_("Former land cover"), choices=(
            (10, _("Cropland")),
            (20, _("Forest land")),
            (30, _("Pasture")),
            (40, _("Shrub land/Grassland (Rangeland)")),
            (50, _("Marginal land")),
            (60, _("Wetland")),
            (70, _("Other land[e.g. developed land – specify in comment field]")),
        ), widget=forms.CheckboxSelectMultiple
    )
    tg_land_cover_comment = forms.CharField(
        required=False, label=_("Additional comments"), widget=CommentInput
    )

    class Meta:
        name = 'former_use'

