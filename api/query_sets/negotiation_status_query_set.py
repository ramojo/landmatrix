from api.query_sets.fake_query_set_with_subquery import FakeQuerySetWithSubquery

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


class NegotiationStatusQuerySet(FakeQuerySetWithSubquery):

    FIELDS = [
        ('name',     'sub.negotiation_status'),
        ('deals',    'COUNT(DISTINCT a.activity_identifier)'),
        ('hectares', 'ROUND(SUM(pi.deal_size))')
    ]
    SUBQUERY_FIELDS = [
        ('negotiation_status', 'pi.negotiation_status'),
    ]
    ORDER_BY = ['sub.negotiation_status']
    GROUP_BY = ['sub.negotiation_status']
