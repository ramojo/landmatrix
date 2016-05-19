from .tags import A_Tag

from django.db import models
from django.contrib.gis.db import models as gismodels

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


class A_Tag_Group(models.Model):
    id = models.AutoField(primary_key=True)
    tg_id = models.IntegerField()
    fk_activity = models.IntegerField()
    fk_a_tag = models.IntegerField(blank=True, null=True)
    geometry = gismodels.GeometryField(srid=4326, spatial_index=True, dim=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    @property
    def tags(self):
        return A_Tag.objects.using('lo').filter(fk_a_tag_group=self.id)

    class Meta:
        db_table = "a_tag_groups"

    def __str__(self):
        return "{} {} {} {} {}".format(self.id, self.tg_id, self.fk_activity, self.fk_a_tag, str(self.tags))


