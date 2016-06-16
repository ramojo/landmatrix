from pprint import pprint
import json

from django.template import loader
from django.http import HttpResponse

from landmatrix.models.country import Country
from landmatrix.models.filter_condition import FILTER_VAR_ACT, \
    FILTER_VAR_INV, FilterCondition
from landmatrix.models.filter_preset import FilterPresetGroup
from api.filters import PresetFilter
from grid.views.browse_condition_form import BrowseConditionForm
from grid.views.save_deal_view import SaveDealView
from grid.widgets import TitleField


__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


def create_condition_formset():
    from django.forms.formsets import formset_factory
    from django.utils.functional import curry

    ConditionFormset = formset_factory(BrowseConditionForm, extra=0)
    ConditionFormset.form = staticmethod(
        curry(BrowseConditionForm, variables_activity=FILTER_VAR_ACT, variables_investor=FILTER_VAR_INV)
    )
    return ConditionFormset


def render_to_response(template_name, context, context_instance):
    """ Returns a HttpResponse whose content is filled with the result of calling
        django.template.loader.render_to_string() with the passed arguments."""
    # Some deprecated arguments were passed - use the legacy code path
    return HttpResponse(render_to_string(template_name, context, context_instance))


def render_to_string(template_name, context, context_instance):
    return loader.render_to_string(template_name, context, context_instance)


def create_variable_table():
    variable_table = []
    group_items = []
    group_title = ''

    for form in SaveDealView.FORMS:
        # FormSet (Spatial Data und Data source)
        if hasattr(form, 'form'):
            form = form.form

        for field_name, field in form.base_fields.items():
            if isinstance(field, TitleField):
                if group_title and group_items:
                    variable_table.append({
                        'label': group_title,
                        'items': group_items,
                    })
                    group_items = []
                group_title = str(field.initial)
            else:
                group_items.append({
                    'name': field_name,
                    'label': str(field.label),
                })

    if group_title and group_items:
        variable_table.append({
            'label': group_title,
            'items': group_items,
        })

    return variable_table


def apply_filters_from_session(request, filter_dict):
    """Reads filter values stored in the current FE user's session and stores
       them in filter_dict. Used in ActivityQuerySet for the grid views and in
       FakeQuerySet for the API calls."""
    for filter in request.session.get('filters', {}).items():
        if 'variable' in filter[1]:
            _update_filters(filter_dict, filter)
        elif 'preset_id' in filter[1]:
            preset = PresetFilter(filter[1].get('preset_id'), filter[1].get('name'))
            for i, condition in enumerate(preset.filter.conditions.all()):
                _update_filters(filter_dict, (filter[1].get('name') + '_{}'.format(i), condition))
    for filter in filters_via_url(request):
        _update_filters(filter_dict, filter)


def filters_via_url(request):
    variable = request.GET.getlist('variable')
    operator = request.GET.getlist('operator')
    value = request.GET.getlist('value')
    return [
        (variable[i], filter_condition(variable[i], operator[i], value[i]))
        for i in range(len(variable))
    ]


def filter_condition(variable, operator, value):
    condition = FilterCondition()
    condition.variable = variable
    condition.operator = operator
    condition.value = value
    return condition


def _update_filters(filter_dict, filter):
    name = _get_filter_type(filter)
    definition = _get_filter_definition(filter)
    definition_key = list(definition.keys())[0]
    if filter[1]['variable'] == 'deal_scope':
        filter_dict['deal_scope'] = filter[1].value
    elif filter_dict[name]['tags'].get(definition_key) and isinstance(filter_dict[name]['tags'][definition_key], list):
        filter_dict[name]['tags'][definition_key].extend(definition[definition_key])
    else:
        filter_dict[name]['tags'].update(definition)


def _get_filter_type(filter_data):
    if filter_data[0] in FILTER_VAR_INV:
        return 'investor'
    return 'activity'


def _get_filter_definition(filter_data):
    """Converts a definition of the form
        {'variable': variable, 'operator': operator, 'value': value}
       as stored in the session and returned when converting a Filter to dict,
       into the format used by FilterToSql:
        {'variable__operator': value}
        """
    variable = filter_data[1]['variable']
    operator = filter_data[1]['operator']
    value = _parse_value(filter_data[1]['value'])

    if 'country' in variable and not value.isnumeric():
        value = str(Country.objects.get(name__iexact=value).pk)
    if 'in' in operator and not isinstance(value, list):
        value = [value]
    return {'{}__{}'.format(variable, operator): value}


def _parse_value(filter_value):
    """Necessary due to the different ways single values and lists are stored in DB and session."""
    if len(filter_value) > 1:
        return filter_value
    if filter_value:
        value = filter_value[0]
    else:
        value = ''
    if '[' in value:
        value = [str(v) for v in json.loads(value)]
    return value
