from django import forms
from django.utils.translation import ugettext_lazy as _

from landmatrix.models.currency import Currency
from grid.widgets import (
    TitleField, CommentInput, NumberInput, NestedMultipleChoiceField,
    YearBasedChoiceField, YearBasedIntegerField, YearBasedNestedMultipleChoiceField
)
from .choices import (
    negotiation_status_choices, implementation_status_choices,
    intention_choices, nature_choices, price_type_choices,
)
from .base_form import BaseForm


__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


class DealGeneralForm(BaseForm):
    # TODO: why not boolean here?
    CONTRACT_FARMING_CHOICES = (
        ("Yes", _("Yes")),
        ("No", _("No")),
    )

    form_title = _('General Info')

    # Land area
    tg_land_area = TitleField(
        required=False, label="", initial=_("Land area"))
    intended_size = forms.IntegerField(
        required=False, label=_("Intended size"), help_text=_("ha"),
        widget=NumberInput)
    contract_size = YearBasedIntegerField(
        required=False,
        label=_("Size under contract (leased or purchased area)"),
        help_text=_("ha"), widget=NumberInput)
    production_size = YearBasedIntegerField(
        required=False, label=_("Size in operation (production)"),
        help_text=_("ha"), widget=NumberInput)
    tg_land_area_comment = forms.CharField(
        required=False, label=_("Land area comments"), widget=CommentInput)

    # Intention of investment
    tg_intention = TitleField(
        required=False, label="", initial=_("Intention of investment"))
    intention = NestedMultipleChoiceField(
        required=False, label=_("Intention of the investment"),
        choices=intention_choices)
    tg_intention_comment = forms.CharField(
        required=False, label=_("Intention of investment comments"),
        widget=CommentInput)

    # Nature of the deal
    tg_nature = TitleField(
        required=False, label="", initial=_("Nature of the deal"))
    nature = forms.MultipleChoiceField(
        required=False, label=_("Nature of the deal"), choices=nature_choices,
        widget=forms.CheckboxSelectMultiple)
    tg_nature_comment = forms.CharField(
        required=False, label=_("Nature of the deal comments"),
        widget=CommentInput)

    # Negotiation status,
    tg_negotiation_status = TitleField(
        required=False, label="", initial=_("Negotiation status")
    )
    negotiation_status = YearBasedChoiceField(
        required=False, label=_("Negotiation status"),
        choices=negotiation_status_choices)
    tg_negotiation_status_comment = forms.CharField(
        required=False, label=_("Negotiation status comments"),
        widget=CommentInput)

    # Implementation status
    tg_implementation_status = TitleField(
        required=False, label="", initial=_("Implementation status"))
    implementation_status = YearBasedChoiceField(
        required=False, label=_("Implementation status"),
        choices=implementation_status_choices)
    tg_implementation_status_comment = forms.CharField(
        required=False, label=_("Implementation status comments"),
        widget=CommentInput)

    # Purchase price
    tg_purchase_price = TitleField(
        required=False, label="", initial=_("Purchase price"))
    purchase_price = forms.DecimalField(
        max_digits=19, decimal_places=2, required=False,
        label=_("Purchase price"))
    purchase_price_currency = forms.ModelChoiceField(
        required=False, label=_("Purchase price currency"),
        queryset=Currency.objects.all().order_by("ranking", "name"))
    purchase_price_type = forms.TypedChoiceField(
        required=False, label=_("Purchase price area type"),
        choices=price_type_choices)
    purchase_price_area = forms.IntegerField(
        required=False, label=_("Purchase price area"), help_text=_("ha"),
        widget=NumberInput(attrs={'class': 'test'}))
    tg_purchase_price_comment = forms.CharField(
        required=False, label=_("Purchase price comments"),
        widget=CommentInput)

    # Leasing fees
    tg_leasing_fees = TitleField(
        required=False, label="", initial=_("Leasing fees"))
    annual_leasing_fee = forms.DecimalField(
        max_digits=19, decimal_places=2, required=False,
        label=_("Annual leasing fee"))
    annual_leasing_fee_currency = forms.ModelChoiceField(
        required=False, label=_("Annual leasing fee currency"),
        queryset=Currency.objects.all().order_by("ranking", "name"))
    annual_leasing_fee_type = forms.TypedChoiceField(
        required=False, label=_("Annual leasing fee type"),
        choices=price_type_choices)
    annual_leasing_fee_area = forms.IntegerField(
        required=False, label=_("Purchase price area"), help_text=_("ha"),
        widget=NumberInput)
    tg_leasing_fees_comment = forms.CharField(
        required=False, label=_("Leasing fees comments"), widget=CommentInput)

    # Contract farming
    tg_contract_farming = TitleField(
        required=False, label="", initial=_("Contract farming"))
    contract_farming = forms.ChoiceField(
        required=False, label=_("Contract farming"),
        choices=CONTRACT_FARMING_CHOICES, widget=forms.RadioSelect)
    on_the_lease = forms.BooleanField(
        required=False, label=_("On leased / purchased area"))
    on_the_lease_area = YearBasedIntegerField(
        required=False, label=_("On leased / purchased area"),
        help_text=_("ha"), widget=NumberInput)
    on_the_lease_farmers = YearBasedIntegerField(
        required=False, label=_("On leased / purchased farmers"),
        help_text=_("farmers"), widget=NumberInput)
    on_the_lease_households = YearBasedIntegerField(
        required=False, label=_("On leased / purchased households"),
        help_text=_("households"), widget=NumberInput)
    off_the_lease = forms.BooleanField(
        required=False, label=_("Not on leased / purchased area (out-grower)"))
    off_the_lease_area = YearBasedIntegerField(
        required=False, label=_("Not on leased / purchased area (out-grower)"),
        help_text=_("ha"), widget=NumberInput)
    off_the_lease_farmers = YearBasedIntegerField(
        required=False,
        label=_("Not on leased / purchased farmers (out-grower)"),
        help_text=_("farmers"), widget=NumberInput)
    off_the_lease_households = YearBasedIntegerField(
        required=False,
        label=_("Not on leased / purchased households (out-grower)"),
        help_text=_("households"), widget=NumberInput)
    tg_contract_farming_comment = forms.CharField(
        required=False, label=_("Contract farming comments"),
        widget=CommentInput)

    class Meta:
        name = 'general_information'
