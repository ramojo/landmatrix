'''
Handle filtering of activities by various datapoints.

Filtering is pretty complex and extends into api, grid, charts, and map views.
We try to collect it here in api where possible....
'''
from collections import OrderedDict
from copy import deepcopy
import operator

from django.utils.translation import ugettext_lazy as _
from django.http import QueryDict

# We can't import from landmatrix.models as FilterCondition imports from here
from landmatrix.models.activity import Activity
from landmatrix.models.country import Country
from landmatrix.models.filter_preset import FilterPreset


FILTER_FORMATS_SQL = 0
FILTER_FORMATS_ELASTICSEARCH = 1


FILTER_VAR_ACT = [
    "target_country", "location", "intention", "intended_size", "contract_size", "production_size",
    "negotiation_status", "implementation_status", "crops", "nature", "contract_farming", "url", "type", "company",
    "type"
]
FILTER_NEW = [
    "agreement_duration", "animals", "annual_leasing_fee", "annual_leasing_fee_area",
    "annual_leasing_fee_currency", "annual_leasing_fee_type", "community_benefits",
    "community_compensation", "community_consultation", "community_reaction",
    "company", "contract_date", "contract_farming", "contract_number", "contract_size",
    "crops", "date", "deal_scope", "domestic_jobs_created", "domestic_jobs_current",
    "domestic_jobs_current_daily_workers", "domestic_jobs_current_employees",
    "domestic_jobs_planned", "domestic_jobs_planned_daily_workers",
    "domestic_jobs_planned_employees", "domestic_use", "email", "export",
    "export_country1", "export_country1_ratio", "export_country2", "export_country2_ratio",
    "export_country3", "file", "foreign_jobs_created", "foreign_jobs_current",
    "foreign_jobs_current_employees", "foreign_jobs_planned", "foreign_jobs_planned_employees",
    "has_domestic_use", "has_export", "implementation_status", "includes_in_country_verified_information",
    "in_country_processing", "intended_size", "intention", "land_cover", "land_owner", "land_use",
    "level_of_accuracy", "location", "minerals", "name", "nature", "negotiation_status", "not_public",
    "not_public_reason", "number_of_displaced_people", "off_the_lease", "off_the_lease_area",
    "off_the_lease_farmers", "on_the_lease", "on_the_lease_area", "on_the_lease_farmers",
    "phone", "point_lat", "point_lon", "production_size", "project_name", "purchase_price",
    "purchase_price_area", "purchase_price_currency", "purchase_price_type",
    "source_of_water_extraction", "target_country", "total_jobs_created", "total_jobs_current",
    "total_jobs_current_daily_workers", "total_jobs_current_employees", "total_jobs_planned",
    "total_jobs_planned_daily_workers", "total_jobs_planned_employees", "type", "url",
    "water_extraction_amount", "water_extraction_envisaged"
]
FILTER_VAR_INV = [
    "investor", "operational_stakeholder", "operational_stakeholder_name",
    "operational_stakeholder_country", "operational_stakeholder_region",
    "country",
]
# Anything in this set is allowed to be passed around in the URL.
FILTER_VARIABLE_NAMES = set(
    FILTER_VAR_ACT + FILTER_NEW + FILTER_VAR_INV + ['status'])

# operation => (numeric operand, character operand, description )
# This is an ordered dict as the keys are used to generate model choices.
# It is here in order to resolve circular imports
FILTER_OPERATION_MAP = OrderedDict([
    ("is", ("= %s", "= '%s'", _("is"))),
    ("in", ("IN (%s)", "IN (%s)", _("is one of"))),
    ("not_in", ("NOT IN (%s)", "NOT IN (%s)", _("isn't any of"))),
    ("gte", (">= %s", ">= '%s'", _("is >="))),
    ("gt", ("> %s", "> '%s'", _("is >"))),
    ("lte", ("<= %s", "<= '%s'", _("is <="))),
    ("lt", ("< %s", "< '%s'", _("is <"))),
    ("contains", (
        "LIKE '%%%%%%%%%s%%%%%%%%'", "LIKE '%%%%%%%%%s%%%%%%%%'",
        _("contains")
    )),
    ("is_empty", ("IS NULL", "IS NULL", _("is empty"))),
])

def get_elasticsearch_match_operation(operator, variable_name, value):
    """ Returns an elasticsearch-conform Match phrase for each SQL-operator """
    if operator == 'is': return ('must', {'match_phrase': {variable_name: value}})
    if operator == 'in': return ('should', {'match_phrase': {variable_name: value}})
    if operator == 'not_in': return ('must_not', {'match_phrase': {variable_name: value}})
    if operator == 'gte': return ('must', {'range': {variable_name: {'gte': value}}})
    if operator == 'gt': return ('must', {'range': {variable_name: {'gt': value}}})
    if operator == 'lte': return ('must', {'range': {variable_name: {'lte': value}}})
    if operator == 'lt': return ('must', {'range': {variable_name: {'lt': value}}})
    if operator == 'contains': return ('must', {'match': {variable_name: value}})
    if operator == 'is_empty': return ('must', {'match_phrase': {variable_name: ''}})

# TODO: this counter is shared by all users, and is per thread.
# It should probably be moved to the session
FILTER_COUNTER = 0


# TODO: convert to object, these don't need to be dicts.
class BaseFilter(dict):
    ACTIVITY_TYPE = 'activity'
    INVESTOR_TYPE = 'investor'

    @property
    def name(self):
        return self['name']

    @property
    def type(self):
        if 'operational_company_' in self['variable']:
            return self.INVESTOR_TYPE
        elif 'parent_stakeholder_' in self['variable']:
            return self.INVESTOR_TYPE
        elif 'parent_investor_' in self['variable']:
            return self.INVESTOR_TYPE
        # Deprecated?
        elif self['variable'] in FILTER_VAR_INV:
            return self.INVESTOR_TYPE
        else:
            return self.ACTIVITY_TYPE


class Filter(BaseFilter):

    def __init__(self, variable, operator, value, name=None, label=None, key=None, display_value=None):
        if operator not in FILTER_OPERATION_MAP:
            raise ValueError('No such operator: {}'.format(operator))

        if not display_value:
            display_value = value

        super().__init__(name=name, variable=variable, operator=operator,
                         value=value, label=label, key=key, display_value=display_value)

    @classmethod
    def from_session(cls, filter_dict):
        '''
        Because filters inherit from dict, they are stored in the session
        as dicts.
        '''
        return cls(
            filter_dict['variable'], filter_dict['operator'],
            filter_dict['value'], name=filter_dict.get('name'),
            label=filter_dict.get('label'), key=filter_dict.get('key'),
            display_value=filter_dict.get('display_value'))

    def to_sql_format(self):
        """
        Converts a filter into the format used by FilterToSql:
        {'variable__operator': value}
        """
        key = self['key'] or 'value'
        # TODO: hopefully _parse_value is no longer required
        value = _parse_value(self['value'], variable=self['variable'], key=key)
        
        if 'in' in self['operator'] and not isinstance(value, list):
            value = [value]

        definition_key = '__'.join((self['variable'], key, self['operator']))
        formatted_filter = {
            definition_key: value,
        }

        return formatted_filter
    
    def to_elasticsearch_match(self):
        """ Will return an elasticsearch operator term and an elasticsearch-format Match or Bool (for multiple matches) dictionary object.
            Example: ('must', {'match': {'intention__value': 3}, '_filter_name': 'intention__value__is'})
            Example2: ('must_not', {'bool': 
                          {'should': [
                              {'match': {'intention__value': 3}},
                              {'match': {'intention__value': 3}}
                          ]},
                       '_filter_name': 'intention__value__not_in'
                      })
            Note: This comes with an added '_filter_name' attribute for internal aggregation which needs to be removed. """
            
        key = self['key'] or 'value'
        # TODO: hopefully _parse_value is no longer required
        value = _parse_value(self['value'], variable=self['variable'], key=key)
        definition_key = '__'.join((self['variable'], key, self['operator']))
        
        # only the starting operator of this match or query-match is important for the logical operation,
        # we now map which one
        elastic_operator = None
        
        if 'in' in self['operator'] and isinstance(value, list) and len(value) > 1: # 
            # generate multiple matches
            matches = []
            inside_operator = None
            for single_value in value:
                operator, partial_match = get_elasticsearch_match_operation(self['operator'], self['variable'], single_value)
                inside_operator = operator
                matches.append(partial_match) 
            match = {'bool': {inside_operator: matches}, '_filter_name': definition_key}
            elastic_operator = 'must' 
            # 'must' is always right here, because the list makes the query already a composite, and the inner operator has effect
        else:
            if isinstance(value, list):
                if len(value) > 1:
                    print('WARNING: converting a filter without "in" with 2 or more values into a single match!')
                value = value[0]
            # generate single value match
            elastic_operator, match = get_elasticsearch_match_operation(self['operator'], self['variable'], value)
            match.update({'_filter_name': definition_key})
        
        return (elastic_operator, match)


class PresetFilter(BaseFilter):

    def __init__(self, preset, name=None, label=None, hidden=False):
        if isinstance(preset, FilterPreset):
            self.preset_id = preset.pk
            self.filter = preset
        else:
            self.preset_id = preset
            self.filter = FilterPreset.objects.get(id=self.preset_id)

        if label is None:
            label = self.filter.name

        super().__init__(name=name, preset_id=self.preset_id, label=label, hidden=hidden)

    @classmethod
    def from_session(cls, filter_dict):
        '''
        Because filters inherit from dict, they are stored in the session
        as dicts.
        '''
        return cls(
            filter_dict['preset_id'], name=filter_dict.get('name'),
            label=filter_dict.get('label'), hidden=filter_dict.get('hidden', False))


def format_filters(filters):
    '''
    Format filters as expected by FilterToSQL and ActivityQueryset.

    We use OrderedDicts here because FilterToSQL code seems to have been
    written on the assumption that dicts are ordered.
    '''
    # TODO: cleanup and move to FilterToSQL
    formatted_filters = {
        'activity': {'tags': OrderedDict()},
        'investor': {'tags': OrderedDict()},
    }

    def _update_filters(filter_dict, filter, group=None):
        name = filter[1].type
        definition = filter[1].to_sql_format()
        definition_key = list(definition.keys())[0]
        if group:
            if group not in filter_dict[name]['tags']:
                filter_dict[name]['tags'][group] = OrderedDict()
            tags = filter_dict[name]['tags'][group]
        else:
            tags = filter_dict[name]['tags']

        if tags.get(definition_key) and isinstance(tags[definition_key], list):
            tags[definition_key].extend(definition[definition_key])
        else:
            tags.update(definition)

    for filter_name, filter_obj in filters.items():
        if isinstance(filter_obj, PresetFilter):
            conditions = filter_obj.filter.conditions.all()
            for i, condition in enumerate(conditions):
                if filter_obj.filter.relation == filter_obj.filter.RELATION_OR:
                    group = filter_obj.filter.name
                else:
                    group = None
                _update_filters(
                    formatted_filters,
                    ('{}_{}'.format(filter_obj.name, i), condition.to_filter()),
                    group=group
                )
        else:
            _update_filters(
                formatted_filters,
                (filter_name, filter_obj)
            )
    return formatted_filters


def format_filters_elasticsearch(filters, initial_query=None):
    """
        Generates an elasticsearch-conform `bool` query from session filters.
        This acts recursively for nested OR filter groups from preset filters
        @param filters: A list of Filter or PresetFilter
        @param query: (Optional) a dict resembling an elasticsearch bool query - filters will be added to this query
            instead of a new query. Use this for recursive calls.
        @return: a dict resembling an elasticsearch bool query, without the "{'bool': query}" wrapper
    """
    from api.elasticsearch import get_elasticsearch_properties
        
    proto_filters = {
        '_filter_name': None,
        'must' : [], # AND
        'filter': [], # EXCLUDE ALL OTHERS
        'must_not': [], # AND NOT
        'should': [], # OR
    }
    query = initial_query or deepcopy(proto_filters)
    
    # TODO: what about 'activity' or 'investor' filter type? (filter_obj.type)
    for filter_obj in filters:
        if isinstance(filter_obj, PresetFilter):
            # we here have multiple filters coming from a preset filter, add them recursively
            preset_filters = [condition.to_filter() for condition in filter_obj.filter.conditions.all()]
            if filter_obj.filter.relation == filter_obj.filter.RELATION_OR:
                # for OR relations we build a new subquery that is ORed and add it to the must matches
                preset_name = filter_obj.filter.name
                # we are constructing a regular query, but because this is an OR order, we will take 
                # all the matches in the 'must' slot and add them to the 'should' list
                or_query = format_filters_elasticsearch(preset_filters)
                query['must'].append({
                    'bool': {
                        'should': or_query['must'] + or_query['should']
                    },
                    '_filter_name': preset_name
                })
            else:
                # for AND relations we just extend the filters into our current query
                format_filters_elasticsearch(preset_filters, initial_query=query)
        else:
            # add a single filter to our query
            # note: 
            if filter_obj['variable'] not in get_elasticsearch_properties('deal').get('properties', {}):
                print('>> Ignored filter variable "%s" because it was not found in the elasticsearch document properties' % filter_obj['variable'])
                continue
            
            # example: ('should', {'match': {'intention__value': 3}, '_filter_name': 'intention__value__not_in'})
            elastic_operator, elastic_match = filter_obj.to_elasticsearch_match()
            
            branch_list = query[elastic_operator]
            current_filter_name = elastic_match['_filter_name']
            existing_match_phrase, existing_i = get_list_element_by_key(branch_list, '_filter_name', current_filter_name)
            # if no filter exists for this yet, add it
            if existing_match_phrase is None:
                branch_list.append(elastic_match)
            else:
                # if match phrase exists for this filter, and it is a bool, add the generated match(es) to its list
                if 'bool' in existing_match_phrase:
                    inside_operator = [key_name for key_name in existing_match_phrase.keys() if not key_name == '_filter_name'][0]
                    if 'bool' in elastic_match:
                        existing_match_phrase[inside_operator].extend(elastic_match[inside_operator])
                    else:
                        existing_match_phrase[inside_operator].append(elastic_match)
                else:
                    # if match phrase exists and is a single match, pop it
                    existing_single_match = branch_list.pop(existing_i)
                    if 'bool' in elastic_match:
                        inside_operator = [key_name for key_name in elastic_match.keys() if not key_name == '_filter_name'][0]
                        # if we have a bool, add the bool, add the popped match to bool
                        elastic_match[inside_operator].append(existing_single_match)
                        query['must'].append(elastic_match)
                    else:
                        # if  we have a single match, make new bool, add popped match and single match
                        matches = [existing_single_match, elastic_match]
                        query['must'].append({'bool': {elastic_operator: matches}, '_filter_name': current_filter_name})
    
    # remove our meta attribute so the query is elaticsearch-conform
    if initial_query is None:
        remove_all_dict_keys_from_mixed_dict(query, '_filter_name')
    return query
    

def load_filters(request, filter_format=FILTER_FORMATS_SQL):
    filters = {}
    session_filters = request.session.get('filters', {}) or {}  # Can be None in some cases
    for filter_name, filter_dict in session_filters.items():
        if 'preset_id' in filter_dict:
            filters[filter_name] = PresetFilter.from_session(filter_dict)
        else:
            filters[filter_name] = Filter.from_session(filter_dict)
    filters.update(load_filters_from_url(request))
    
    if filter_format == FILTER_FORMATS_ELASTICSEARCH:
        # note: passing only Filters, not (name, filter) dict!
        formatted_filters = format_filters_elasticsearch(filters.values())
    else:
        formatted_filters = format_filters(filters)#, filter_format=filter_format)

    return formatted_filters


def load_filters_from_url(request):
    '''
    Read any querystring param filters. Preset filters not allowed.
    '''
    variables = request.GET.getlist('variable')
    operators = request.GET.getlist('operator')
    values = request.GET.getlist('value')
    combined = zip(variables, operators, values)

    filters = {f[0]: Filter(f[0], f[1], f[2]) for f in combined}

    return filters


def load_statuses_from_url(request):
    if 'status' in request.GET:
        statuses = []
        if request.user.is_authenticated() and request.user.is_staff:
            # Staff can view all statuses
            allowed = set(map(
                operator.itemgetter(0), Activity.STATUS_CHOICES))
        else:
            allowed = set(Activity.PUBLIC_STATUSES)

        for status in request.GET.getlist('status'):
            try:
                status = int(status)
            except (ValueError, TypeError):
                continue

            if status in allowed:
                statuses.append(status)

    else:
        statuses = Activity.PUBLIC_STATUSES

    return statuses


def clean_filter_query_string(request):
    whitelist = QueryDict(mutable=True)
    has_allowed_param = any(
        key in request.GET for key in FILTER_VARIABLE_NAMES)

    if request.GET and has_allowed_param:
        for key in request.GET.keys():
            if key in FILTER_VARIABLE_NAMES:
                whitelist.setlist(key, request.GET.getlist(key))

    return whitelist


def _parse_value(filter_value, variable=None, key=None):
    """
    Necessary due to the different ways single values and lists are stored
    in DB and session.
    """
    if len(filter_value) > 1:
        return filter_value
    if filter_value:
        value = filter_value[0]
    else:
        value = ''
    if '[' in value:
        value = [str(v) for v in json.loads(value)]
    
    if variable is not None and key is not None:
        # Is this still required? Why not just always store ids?
        is_country_string = (
            'country' in variable and
            key == 'value' and
            not value.isnumeric()
        )
        if is_country_string:
            country = Country.objects.defer('geom').get(name__iexact=value.replace('-', ' '))
            value = str(country.pk)
    
    return value


def get_list_element_by_key(the_list, key, value):
    """ returns the *first* dictionary in a list whose value of a key matches the given value, or None """
    if value is not None and not value == '':
        for i, dict_element in enumerate(the_list):
            if dict_element.get(key, None) == value:
                return dict_element, i
    return None, None

def remove_all_dict_keys_from_mixed_dict(maybe_dict, key_name):
    """ Recursively removes all occurences of one key from a dictionary. The recursion if continued in all lists the dictionary contains """
    if isinstance(maybe_dict, dict):
        if key_name in maybe_dict:
            del maybe_dict[key_name]
        for obj in maybe_dict.values():
            remove_all_dict_keys_from_mixed_dict(obj, key_name)
    elif isinstance(maybe_dict, list):
        for obj in maybe_dict:
            remove_all_dict_keys_from_mixed_dict(obj, key_name)
