
__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

from django.db import models
from django.utils.translation import ugettext_lazy as _


class CountryManager(models.Manager):

    def get_target_countries_by_activity(self, activity):
        '''
        Seems like there should be a way to do this using PostgreSQL hvals
        but it doesn't seem like django-hstore has implemented it.
        '''
        attribute_groups = activity.activityattributegroup_set.filter(
            attributes__contains=['target_country'])
        country_ids = {
            int(attribute_group.attributes['target_country'])
            for attribute_group in attribute_groups
        }
        matching_countries = self.filter(pk__in=country_ids)

        return matching_countries


class Country(models.Model):

    fk_region = models.ForeignKey("Region", verbose_name=_("Region"))
    code_alpha2 = models.CharField(_("Code ISO 3166-1 alpha2"), max_length=2)
    code_alpha3 = models.CharField(_("Code ISO 3166-1 alpha3"), max_length=3)
    name = models.CharField("Name", max_length=255)
    slug = models.SlugField("Slug", max_length=100)
    point_lat = models.DecimalField(
        _("Latitude of central point"), max_digits=18, decimal_places=12, blank=True, null=True
    )
    point_lon = models.DecimalField(
        _("Longitude of central point"), max_digits=18, decimal_places=12, blank=True, null=True
    )
    point_lat_min = models.DecimalField(
        _("Latitude of northernmost point"), max_digits=18, decimal_places=12, blank=True, null=True
    )
    point_lon_min = models.DecimalField(
        _("Longitude of westernmost point"), max_digits=18, decimal_places=12, blank=True, null=True
    )
    point_lat_max = models.DecimalField(
        _("Latitude of southernmost point"), max_digits=18, decimal_places=12, blank=True, null=True
    )
    point_lon_max = models.DecimalField(
        _("Longitude of easternmost point"), max_digits=18, decimal_places=12, blank=True, null=True
    )
    democracy_index = models.DecimalField(
        _("Democracy index"), max_digits=3, decimal_places=2, blank=True, null=True
    )
    corruption_perception_index = models.DecimalField(
        _("Corruption perception index"), max_digits=2, decimal_places=1, blank=True, null=True
    )
    high_income = models.BooleanField(_("High income"), default=False)
    is_target_country = models.BooleanField(_("Is target country"), default=False)

    objects = CountryManager()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name', )
