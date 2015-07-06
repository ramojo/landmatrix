__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

from django.conf import settings

from landmatrix.models import *

def list_view_wanted(filters):
    group = filters.get("group_by", "")
    group_value = filters.get("group_value", "")
    return group == "all" or group_value

def get_join_columns(columns, group, group_value):
    if group_value and group not in columns:
        join_columns = columns[:]
        join_columns.append(group)
    else:
        join_columns = columns
    return join_columns

def join(table_or_model, alias, on):
    if not isinstance(table_or_model, str):
        table_or_model = table_or_model._meta.db_table
    return "LEFT JOIN %s AS %s ON %s " % (table_or_model, alias, on)

def join_expression(table_or_model, alias, local_field, foreign_field='id'):
    return join(
        table_or_model, alias,
        "%s = %s.%s"   % (local_field, alias, foreign_field)
    )

def join_attributes(alias, attribute='', attributes_model=ActivityAttributeGroup, attribute_field='fk_activity_id'):
    if not attribute: attribute = alias
    return join(
        attributes_model, alias,
        "(a.id = %s.%s AND %s.attributes ? '%s')" % (alias, attribute_field, alias, attribute)
    )

def join_activity_attributes(alias, attribute):
    return join(
        ActivityAttributeGroup, alias,
        on="a.activity_identifier = %s.activity_identifier AND %s.attributes ? '%s'" % (alias, alias, attribute)
    )

class SQLBuilder:

    @classmethod
    def create(cls, columns, filters):
        from .list_sql_builder import ListSQLBuilder
        from .group_sql_builder import GroupSQLBuilder
        if list_view_wanted(filters):
            return ListSQLBuilder(filters, columns)
        else:
            return GroupSQLBuilder(filters, columns)

    def __init__(self, filters, columns):
        self.filters = filters
        self.columns = columns
        self.group = filters.get("group_by", "")
        self.group_value = filters.get("group_value", "")

    def get_from_sql(self):

        self.join_expressions = []

        if self._need_involvements_and_stakeholders():
            self.join_expressions.extend([
                join_expression(Involvement, 'i', 'a.id', 'fk_activity_id'),
                join_expression(Stakeholder, 's', 'i.fk_stakeholder_id')
            ])

        for c in get_join_columns(self.columns, self.group, self.group_value):
            self._add_join_for_column(c)

        return "\n".join(self.join_expressions)

    GROUP_TO_NAME = {
        'all':              "'all deals'",
        'target_region':    'deal_region.name',
        'target_country':   'deal_country.name',
        'year':             'pi_negotiation_status.year',
        'crop':             'crop.name',
        'intention':        'intention.value',
        'investor_region':  'investor_region.name',
        'investor_country': 'investor_country.name',
        'investor_name':    'investor_name.value',
        'data_source_type': 'data_source_type.value'
    }
    def get_name_sql(self):
        return self.GROUP_TO_NAME.get(self.group, "'%s'" % self.group)

    def get_where_sql(self):
        raise RuntimeError('SQLBuilder.get_where_sql() not implemented')

    def get_group_sql(self):
        raise RuntimeError('SQLBuilder.get_group_sql() not implemented')

    def get_inner_group_sql(self):
        return ''

    def get_columns_sql(self):
        return "\n".join(map(lambda c: self.column_sql(c), self.columns))

    def get_sub_columns_sql(self):
        return ''

    @classmethod
    def get_base_sql(cls):
        raise RuntimeError('SQLBuilder.get_base_sql() not implemented')

    def _need_involvements_and_stakeholders(self):
        return 'investor' in self.filters or any(
            x in ("investor_country","investor_region", "investor_name", 'primary_investor', "primary_investor_name")
            for x in self.columns
        )

    COLUMNS = { }
    def _setup_column_sql(self):
        if self.COLUMNS: return
        self.COLUMNS = {

            'intended_size': [], 'contract_size': [], 'production_size': [],

            'investor_country':   (
                'investor_country', [
                    join_attributes(
                        'skvl1', 'country',
                        attributes_model=StakeholderAttributeGroup, attribute_field='fk_stakeholder_id'
                    ),
                    join(
                        Country, 'investor_country',
                        on="investor_country.id = CAST(skvl1.attributes->'country' AS numeric)"
                    ),
                    join_expression(Region, 'investor_region', 'investor_country.fk_region_id')
                ]
            ),

            'investor_name':      [
                join_attributes(
                    'investor_name',
                    attributes_model=StakeholderAttributeGroup, attribute_field='fk_stakeholder_id'
                )
            ],

            'crop':               [
                join_attributes('akvl1', 'crops'),
                join_expression('crops', 'crop', 'akvl1.value')
            ],

            'target_country':     (
                'target_country', [
                    join_attributes('target_country'),
                    join(
                        Country, 'deal_country',
                        on="CAST(target_country.attributes->'target_country' AS numeric) = deal_country.id"
                    ),
                    join_expression(Region, 'deal_region', 'deal_country.fk_region_id')
                ]
            ),

            'primary_investor':   [ join_expression(PrimaryInvestor, 'p', 'i.fk_primary_investor_id') ],

            'data_source_type':   ( 'data_source', [ join_activity_attributes('data_source_type', 'type') ] ),

            'data_source':        [
                join_activity_attributes('data_source_type', 'type'),
                join_activity_attributes('data_source_url', 'url'),
                join_activity_attributes('data_source_organisation', 'company'),
                join_activity_attributes('data_source_date', 'date'),
            ],

            'contract_farming':   [ join_activity_attributes('contract_farming', 'off_the_lease'), ],

            'nature_of_the_deal': [ join_activity_attributes('nature_of_the_deal', 'nature'), ],

            'latlon':             [
                join_activity_attributes('latitude', 'point_lat'),
                join_activity_attributes('longitude', 'point_lon'),
                join_activity_attributes('level_of_accuracy', 'level_of_accuracy'),
            ],
        }
        self.COLUMNS['investor_region'] = self.COLUMNS['investor_country']
        self.COLUMNS['target_region'] = self.COLUMNS['target_country']

    def _add_join_for_column(self, c):
        self._setup_column_sql()
        spec = self.COLUMNS.get(c, [join_attributes(c)])
        if isinstance(spec, tuple):
            if not any(spec[0] in string for string in self.join_expressions):
                self.join_expressions.extend(spec[1])
        else:
            self.join_expressions.extend(spec)

    SQL_COLUMN_MAP = {
        "investor_name": ["array_to_string(array_agg(DISTINCT concat(investor_name.attributes->'investor_name', '#!#', s.stakeholder_identifier)), '##!##') as investor_name,",
                          "CONCAT(investor_name.value, '#!#', s.stakeholder_identifier) as investor_name,"],
        "investor_country": ["array_to_string(array_agg(DISTINCT concat(investor_country.name, '#!#', investor_country.code_alpha3)), '##!##') as investor_country,",
                             "CONCAT(investor_country.name, '#!#', investor_country.code_alpha3) as investor_country,"],
        "investor_region": ["GROUP_CONCAT(DISTINCT CONCAT(investor_region.name, '#!#', investor_region.id) SEPARATOR '##!##') as investor_region,",
                            "CONCAT(investor_region.name, '#!#', investor_region.id) as investor_region,"],
        "intention": ["array_to_string(array_agg(DISTINCT intention.attributes->'intention' ORDER BY intention.attributes->'intention'), '##!##') AS intention,",
                      "intention.value AS intention,"],
        "crop": ["GROUP_CONCAT(DISTINCT CONCAT(crop.name, '#!#', crop.code ) SEPARATOR '##!##') AS crop,",
                 "CONCAT(crop.name, '#!#', crop.code ) AS crop,"],
        "deal_availability": ["a.availability AS availability, ", "a.availability AS availability, "],
        "data_source_type": ["GROUP_CONCAT(DISTINCT CONCAT(data_source_type.value, '#!#', data_source_type.group) SEPARATOR '##!##') AS data_source_type, ",
                             " data_source_type.value AS data_source_type, "],
        "target_country": [" array_to_string(array_agg(DISTINCT deal_country.name), '##!##') as target_country, ",
                           " deal_country.name as target_country, "],
        "target_region": ["GROUP_CONCAT(DISTINCT deal_region.name SEPARATOR '##!##') as target_region, ",
                          " deal_region.name as target_region, "],
        "deal_size": ["IFNULL(pi_deal_size.value, 0) + 0 AS deal_size,",
                      "IFNULL(pi_deal_size.value, 0) + 0 AS deal_size,"],
        "year": ["pi_negotiation_status.year AS year, ", "pi_negotiation_status.year AS year, "],
        "deal_count": ["COUNT(DISTINCT a.activity_identifier) as deal_count,",
                       "COUNT(DISTINCT a.activity_identifier) as deal_count,"],
        "availability": ["SUM(a.availability) / COUNT(a.activity_identifier) as availability,",
                         "SUM(a.availability) / COUNT(a.activity_identifier) as availability,"],
        "primary_investor": ["array_to_string(array_agg(DISTINCT p.name), '##!##') as primary_investor,",
                             "array_to_string(array_agg(DISTINCT p.name), '##!##') as primary_investor,"],
        "negotiation_status": [
            """array_to_string(
                    array_agg(
                        DISTINCT concat(
                            negotiation_status.attributes->'negotiation_status',
                            '#!#',
                            COALESCE(EXTRACT(YEAR FROM negotiation_status.date), 0)
                        )
                    ),
                    '##!##'
                ) as negotiation_status,"""
        ],
        "implementation_status": [
            """array_to_string(
                    array_agg(
                        DISTINCT concat(
                            implementation_status.attributes->'implementation_status',
                            '#!#',
                            COALESCE(EXTRACT(YEAR FROM implementation_status.date), 0)
                        )
                    ),
                    '##!##'
                ) as implementation_status,"""
        ],
        "nature_of_the_deal": ["array_to_string(array_agg(DISTINCT nature_of_the_deal.value), '##!##') as nature_of_the_deal,"],
        "data_source": ["GROUP_CONCAT(DISTINCT CONCAT(data_source_type.value, '#!#', data_source_type.group) SEPARATOR '##!##') AS data_source_type, GROUP_CONCAT(DISTINCT CONCAT(data_source_url.value, '#!#', data_source_url.group) SEPARATOR '##!##') as data_source_url, GROUP_CONCAT(DISTINCT CONCAT(data_source_date.value, '#!#', data_source_date.group) SEPARATOR '##!##') as data_source_date, GROUP_CONCAT(DISTINCT CONCAT(data_source_organisation.value, '#!#', data_source_organisation.group) SEPARATOR '##!##') as data_source_organisation,"],
        "contract_farming": ["array_to_string(array_agg(DISTINCT contract_farming.value), '##!##') as contract_farming,"],
        "intended_size": ["0 AS intended_size,"],
        "contract_size": ["0 AS contract_size,"],
        "production_size": ["0 AS production_size,"],
        "location": ["array_to_string(array_agg(DISTINCT location.value), '##!##') AS location,"],
        "deal_id": ["a.activity_identifier as deal_id,", "a.activity_identifier as deal_id,"],
        "latlon": ["GROUP_CONCAT(DISTINCT CONCAT(latitude.value, '#!#', longitude.value, '#!#', level_of_accuracy.value) SEPARATOR '##!##') as latlon,"],
    }
#             AND (intention.value IS NULL OR intention.value != 'Mining')

