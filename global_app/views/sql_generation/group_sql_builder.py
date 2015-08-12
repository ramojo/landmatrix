__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

from global_app.views.sql_generation.sql_builder import SQLBuilder

class GroupSQLBuilder(SQLBuilder):

    def get_where_sql(self):
        where = []

#        if 'intention' in self.columns:
#            where.append("AND (intention.attributes->'intention') IS NOT NULL")

        if self.filters.get("starts_with", None):
            starts_with = self.filters.get("starts_with", "").lower()
            if self.group == "investor_country":
                where.append("AND investor_country.slug like '%s%%%%' " % starts_with)
            elif self.group == "target_country":
                where.append("AND deal_country.slug like '%s%%%%' " % starts_with)
            else:
                where.append("AND trim(lower(%s.value)) like '%s%%%%' " % (self.group, starts_with))

        return '\n'.join(where)


    def get_group_sql(self):
        group_by = [self.group if self.group else 'dummy', self.get_name_sql()]
        for c in self.columns:
            if not c in group_by:
                if not any(f in self.column_sql(c) for f in ('ARRAY_AGG', 'COUNT')):
                    group_by.append(c)
        return "GROUP BY %s" % ', '.join(group_by)
        if self.group:  return "GROUP BY %s" % self.group
        else:           return 'GROUP BY dummy'

    def get_inner_group_sql(self):
        # query deals grouped by a key
        return ", %s" % self.group

    def column_sql(self, c):
        if c == self.group:
            # use single values for column which gets grouped by
            return self.SQL_COLUMN_MAP.get(c)[1]
        return self.SQL_COLUMN_MAP.get(c)[0]

    @classmethod
    def get_base_sql(cls):
        return u"""SELECT DISTINCT
              %(name)s as name,
              %(columns)s,'dummy' as dummy
FROM landmatrix_activity                    AS a
%(from)s
LEFT JOIN landmatrix_activityattributegroup AS pi_deal    ON a.id = pi_deal.fk_activity_id AND  pi_deal.attributes ? 'pi_deal'
LEFT JOIN landmatrix_activityattributegroup AS deal_scope ON a.id = deal_scope.fk_activity_id AND deal_scope.attributes ? 'deal_scope'
%(from_filter)s
WHERE """ + "\nAND ".join([ cls.max_version_condition(), cls.status_active_condition(), cls.is_deal_condition(), cls.not_mining_condition() ]) + """
%(where)s
%(where_filter)s
%(group_by)s
%(order_by)s
%(limit)s"""