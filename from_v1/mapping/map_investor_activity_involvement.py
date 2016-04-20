from mapping.map_model import MapModel
import landmatrix.models
import old_editor.models
from migrate import V1
from mapping.map_activity import MapActivity
from mapping.map_investor import MapInvestor
from mapping.aux_functions import get_now

from django.db import connections

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


def get_status_for_investor(primary_investor_id):
    investor = old_editor.models.PrimaryInvestor.objects.using(V1).get(pk=primary_investor_id)
    return investor.fk_status.pk


class MapInvestorActivityInvolvement(MapModel):
    old_class = old_editor.models.Involvement
    new_class = landmatrix.models.InvestorActivityInvolvement
    attributes = {
        'investment_ratio': 'percentage',
        'fk_primary_investor_id': ('fk_investor_id', ('fk_status_id', get_status_for_investor), ('timestamp', get_now))
    }
    depends = [ MapActivity, MapInvestor ]

    @classmethod
    def all_records(cls):
        activity_ids = MapActivity.all_ids()
        stakeholder_ids = cls.all_stakeholder_ids()
        primary_investor_ids = MapInvestor.all_ids()
        records = cls.old_class.objects.using(V1).\
            filter(fk_activity__in=activity_ids).\
            filter(fk_stakeholder__in=stakeholder_ids).\
            filter(fk_primary_investor__in=primary_investor_ids).values()
        cls._count = len(records)
        # print('all_records', records)
        return records

    @classmethod
    def all_stakeholder_ids(cls):

        cursor = connections[V1].cursor()
        cursor.execute("""
SELECT id
FROM stakeholders AS s
WHERE version = (SELECT MAX(version) FROM stakeholders WHERE stakeholder_identifier = s.stakeholder_identifier)
ORDER BY stakeholder_identifier
        """)
        return [id[0] for id in cursor.fetchall()]

