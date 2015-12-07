from api.query_sets.fake_query_set_with_subquery import FakeQuerySetWithSubquery

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

from api.query_sets.fake_query_set import FakeQuerySet
from global_app.forms.add_deal_general_form import AddDealGeneralForm


class IntentionQuerySet(FakeQuerySetWithSubquery):

    FIELDS = [
        ('intention', 'sub.intention'),
        ('deal_count',         'COUNT(DISTINCT a.activity_identifier)'),
        ('deal_size',          "ROUND(SUM(pi.deal_size))")
    ]
    SUBQUERY_FIELDS = [
        ('intention', """CASE
            WHEN COUNT(DISTINCT intention.attributes->'intention') > 1 THEN 'Multiple intention'
            ELSE intention.attributes->'intention'
        END""")
    ]
    ADDITIONAL_JOINS = [
        "LEFT JOIN landmatrix_activityattributegroup    AS intention        ON a.id = intention.fk_activity_id AND intention.attributes ? 'intention'",
    ]
    GROUP_BY = ['sub.intention']
    ORDER_BY = ['sub.intention']
    ADDITIONAL_SUBQUERY_OPTIONS = "GROUP BY a.id, intention.attributes->'intention'"

    def __init__(self, get_data):
        super().__init__(get_data)
        self.intention = get_data.get("intention", "")

    INTENTIONS = list(filter(lambda k: "Mining" not in k, [str(i[1]) for i in AddDealGeneralForm().fields["intention"].choices]))
    INTENTIONS_AGRICULTURE = [str(i[1]) for i in AddDealGeneralForm().fields["intention"].choices[0][2]]

    def all(self):
        parent_intention = self.intention
        filter_intentions = parent_intention.lower() == "agriculture" and self.INTENTIONS_AGRICULTURE[:] or self.INTENTIONS[:]
        filter_intentions.append("Multiple intention")

        intention_filter_sql = "\nAND (intention.attributes->'intention' IN ('%s')\nOR intention.attributes->'intention' = '')" % "', '".join(filter_intentions)
        self._filter_sql += intention_filter_sql

        found = FakeQuerySet.all(self)

        intentions = {}

        for i in found:
             name = i['intention'] or ""
             name = (name == "Agriunspecified" and "Non-specified") or (name == "Other (please specify)" and "Other") or name
             intentions[name] = {
                 "name": name,
                 "deals": i['deal_count'],
                 "hectares": i['deal_size'],
             }
        output = []
        for i in filter_intentions:
            i = (i == "Agriunspecified" and "Non-specified") or (i == "Other (please specify)" and "Other") or i
            output.append(intentions.get(i, {"name": i, "deals": 0, "hectares": 0}))
        output.append(intentions.get("", {"name": "", "deals": 0, "hectares": 0}))
        return output