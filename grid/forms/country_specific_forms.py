from django import forms
from django.utils.translation import ugettext_lazy as _

from landmatrix.models import Country, ActivityAttribute
from grid.forms.base_form import BaseForm
from grid.widgets import TitleField, NumberInput


def get_country_specific_form_classes(activity, data=None, files=None):
    for target_country_slug in _get_deal_target_country_slugs(activity):
        try:
            form_class = COUNTRY_SPECIFIC_FORMS[target_country_slug]
        except KeyError:
            pass
        else:
            yield form_class


def _get_deal_target_country_slugs(activity):
    # Activity may also be an ActivityHistory instance
    # (from django-simple-history) hence the weird query below.
    # TODO: move to models, once I understand things a bit better
    country = ActivityAttribute.objects.filter(
        fk_activity_id=activity.id, name='target_country')

    if country.count() > 0:
        country_id = country.first().value
        try:
            target_country = Country.objects.get(id=country_id)
        except Country.DoesNotExist:
            pass
        else:
            yield target_country.slug


class GermanyForm(BaseForm):
    '''
    This is just a simple example.
    '''
    form_title = _('Germany')
    tg_land_area = TitleField(required=False, label="", initial=_("Land area"))
    intended_size = forms.IntegerField(
        required=False, label=_("Intended size"), help_text=_("ha"),
        widget=NumberInput)
    test_integer = forms.IntegerField(
        required=False, label=_("Test integer"), widget=NumberInput)

    class Meta:
        name = 'germany specific info'


COUNTRY_SPECIFIC_FORMS = {
    'germany': GermanyForm,
}
