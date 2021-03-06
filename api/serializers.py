from collections import OrderedDict

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import GEOSGeometry
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from landmatrix.models import (
    Activity, InvestorVentureInvolvement, FilterPreset,
)


class PassThruSerializer(serializers.BaseSerializer):
    '''
    Read only serializer that does nothing, just passed the JSON object
    we already have through.
    '''
    def to_representation(self, obj):
        return obj


class FilterPresetSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilterPreset
        exclude = ('is_default', 'overrides_default')


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return obj.get_full_name()

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'full_name')


class RegionSerializer(serializers.BaseSerializer):
    '''
    Returns a region as a list: [id, slug, title].
    '''
    def to_representation(self, obj):
        return [obj.region.id, obj.region.slug, obj.title]


class DealLocationSerializer(serializers.Serializer):
    point_lat = serializers.DecimalField(max_digits=11, decimal_places=8)
    point_lon = serializers.DecimalField(max_digits=11, decimal_places=8)
    contract_area = GeometryField()
    intended_area = GeometryField()
    production_area = GeometryField()

    def to_representation(self, obj):
        '''
        Convert our binary polygon representation to a GEOSGeometry.
        '''
        # TODO: DRY, we should have a model with a list of these fields
        for geo_field in ('contract_area', 'intended_area', 'production_area'):
            if geo_field in obj and obj[geo_field]:
                if not isinstance(obj[geo_field], GEOSGeometry):
                    obj[geo_field] = GEOSGeometry(obj[geo_field], srid=4326)

        return super().to_representation(obj)


class DealSerializer(serializers.Serializer):
    '''
    Used to serialize the deal list view.
    '''
    deal_id = serializers.IntegerField()
    intention = serializers.CharField()
    intended_size = serializers.IntegerField()
    contract_size = serializers.IntegerField()
    production_size = serializers.IntegerField()
    investor = serializers.CharField()
    locations = serializers.ListField(child=DealLocationSerializer())

    def to_representation(self, obj):
        locations = []
        location_fields = self.fields['locations'].child.fields.keys()
        array_elements = [obj[field] for field in location_fields]
        split_elements = [elem.split(';') for elem in array_elements]

        for values in zip(*split_elements):
            location = {}
            for field_name, value in zip(location_fields, values):
                location[field_name] = value or None

            locations.append(location)

        # For our intfields, we sometimes get unexpected floats. Round those.
        for field in ('contract_size', 'intended_size', 'production_size'):
            value = obj[field]
            if isinstance(value, str):
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = round(float(value))
                    except ValueError:
                        value = None
                obj[field] = value

        obj['locations'] = locations

        return super().to_representation(obj)


class DealDetailSerializer(serializers.ModelSerializer):
    '''
    Returns deal attributes.
    '''
    attributes = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = (
            'activity_identifier', 'fk_status', 'is_public',
            'deal_scope', 'negotiation_status', 'implementation_status',
            'deal_size', 'attributes'
        )

    def get_attributes(self, obj):
        return obj.attributes_as_dict


class InvestorNetworkSerializer(serializers.BaseSerializer):
    '''
    This serializer takes an investor and outputs a list of involvements
    formatted like:
    {
        "id": 123,
        "name": "",
        "country": "",
        "classification": "",
        "parent_relation": "",
        "homepage": "",
        "opencorporates_link": "",
        "comment": "",
        "stakeholders": [
            {
                "id": 345,
                "name": "",
                [...] 
                "involvement": [
                    "parent_type": "stakeholder" // or "investor"
                    "percentage": "",
                    "investment_type": "",
                    "loans_amount": "",
                    "loans_currency": "",
                    "loans_date": "",
                    "comment": "",
                ],
                "stakeholders": [],
            },
            [...]
        ],
    }
    This is not REST, but it maintains compatibility with the existing API.
    '''

    def to_representation(self, obj, parent_types=['parent_stakeholders', 'parent_investors']):
        response = {
            "id": obj.id,
            "name": obj.name,
            "country": str(obj.fk_country),
            "classification": obj.get_classification_display(),
            "parent_relation": obj.get_parent_relation_display(),
            "homepage": obj.homepage,
            "opencorporates_link": obj.opencorporates_link,
            "comment": obj.comment,
            "stakeholders": [],
        }
        involvements = InvestorVentureInvolvement.objects.filter(fk_venture=obj)
        for parent_type in parent_types:
            parents = []
            if parent_type == 'parent_investors':
                parent_involvements = involvements.investors()
            else:
                parent_involvements = involvements.stakeholders()
            for i, involvement in enumerate(parent_involvements):
                parent = self.to_representation(involvement.fk_investor, parent_types)
                parent["parent_type"] = parent_type == 'parent_investors' and 'investor' or 'stakeholder'
                parent["involvement"] = {
                    "percentage": involvement.percentage,
                    "investment_type": involvement.get_investment_type_display(),
                    "loans_amount": involvement.loans_amount,
                    "loans_currency": str(involvement.loans_currency),
                    "loans_date": involvement.loans_date,
                    "comment": involvement.comment,
                }
                parents.append(parent)
            response['stakeholders'].extend(parents)

        return response


class NegotiationStatusSerializer(serializers.Serializer):
    name = serializers.CharField()
    deals = serializers.IntegerField()
    hectares = serializers.IntegerField()
