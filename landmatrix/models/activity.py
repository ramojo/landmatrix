from django.db import models
from django.utils.translation import ugettext_lazy as _
from landmatrix.models.defaultstringrepresentation import DefaultStringRepresentation

__author__ = 'lene'


class Activity(DefaultStringRepresentation, models.Model):
    activity_identifier = models.IntegerField(_("Activity identifier"), db_index=True)
    version = models.IntegerField(_("Version"), db_index=True)
    availability = models.FloatField(_("availability"), blank=True, null=True)
    fully_updated = models.DateTimeField(_("Fully updated"), blank=True, null=True)