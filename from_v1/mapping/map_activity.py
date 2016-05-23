from mapping.map_model import MapModel
from mapping.map_status import MapStatus
import landmatrix.models
import old_editor.models
from migrate import V1, V2

from django.db import connections
from django.utils import timezone
from datetime import timedelta, datetime

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


class MapActivity(MapModel):
    old_class = old_editor.models.Activity
    new_class = landmatrix.models.Activity
    depends = [ MapStatus ]

    @classmethod
    def all_records(cls):
        ids = cls.all_ids()
        cls._count = len(ids)
        return cls.old_class.objects.using(V1).filter(pk__in=ids).values()

    @classmethod
    def all_ids(cls):
        cursor = connections[V1].cursor()
        cursor.execute("""
SELECT id
FROM activities AS a
WHERE version = (SELECT MAX(version) FROM activities WHERE activity_identifier = a.activity_identifier)
--                                                                         AND activity_identifier = 3538
ORDER BY activity_identifier
        """)
        return [id[0] for id in cursor.fetchall()]

    @classmethod
    def save_record(cls, new, save):
        """Save all versions of an activity as HistoricalActivity records."""
        if not save:
            return

        versions = get_activity_versions(new)
        for i, version in enumerate(versions):
            if not version['id'] == new.id:
                landmatrix.models.Activity.history.using(V2).create(
                    id=version['id'],
                    activity_identifier=version['activity_identifier'],
                    availability=version['availability'],
                    fk_status_id=version['fk_status_id'],
                    fully_updated=version['fully_updated'],
                    history_date=calculate_history_date(versions, i),
                    history_user=get_history_user(version)
                )
        new.save(using=V2)


def calculate_history_date(versions, i):
    if i >= len(versions):
        return datetime(2000, 1, 1, tzinfo=timezone.now().tzinfo)
    if versions[i].get('fully_updated'):
        return versions[i]['fully_updated']
    if versions[i].get('timestamp_review'):
        return timezone.make_aware(versions[i]['timestamp_review'], timezone.get_current_timezone())
    changeset = get_changeset(versions[i])
    if changeset:
        return changeset.timestamp
    # could not find any time information. use next newer version and arbitrarily subtract 1 minute.
    return calculate_history_date(versions, i+1) - timedelta(minutes=1)


def get_changeset(activity_record):
    return old_editor.models.A_Changeset.objects.using(V1).filter(
        fk_activity=activity_record['id']
    ).last()


def get_activity_versions(activity):
    cursor = connections[V1].cursor()
    cursor.execute(
        """SELECT id FROM activities AS a WHERE activity_identifier = {}
        ORDER BY version """.format(activity.activity_identifier)
    )
    ids = [id[0] for id in cursor.fetchall()]
    return MapActivity.old_class.objects.using(V1).filter(pk__in=ids).values()

def get_history_user(activity_record):
    changeset = get_changeset(activity_record)
    if changeset:
        return changeset.fk_user