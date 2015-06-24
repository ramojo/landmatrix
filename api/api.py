__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

from tastypie import fields
from tastypie.resources import ModelResource
from landmatrix.models import Involvement, Activity, Stakeholder, PrimaryInvestor, Status, ActivityAttributeGroup


class StatusResource(ModelResource):
    class Meta:
        queryset = Status.objects.all()

class ActivityResource(ModelResource):
    fk_status = fields.ForeignKey(StatusResource, attribute='fk_status')
    class Meta:
        queryset = Activity.objects.all()

class StakeholderResource(ModelResource):
    fk_status = fields.ForeignKey(StatusResource, attribute='fk_status')
    class Meta:
        queryset = Stakeholder.objects.all()

class PrimaryInvestorResource(ModelResource):
    fk_status = fields.ForeignKey(StatusResource, attribute='fk_status')
    class Meta:
        queryset = PrimaryInvestor.objects.all()

class InvolvementResource(ModelResource):
    fk_activity = fields.ForeignKey(ActivityResource, attribute='fk_activity')
    fk_stakeholder = fields.ForeignKey(StakeholderResource, attribute='fk_stakeholder')
    fk_primary_investor = fields.ForeignKey(StakeholderResource, attribute='fk_primary_investor')
    class Meta:
        queryset = Involvement.objects.all()

class ActivityAttributeGroupResource(ModelResource):
    fk_activity = fields.ForeignKey(ActivityResource, attribute='fk_activity')
    class Meta:
        queryset = ActivityAttributeGroup.objects.all()
