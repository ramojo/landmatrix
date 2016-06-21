from django.utils.translation import ugettext as _
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

from landmatrix.models.filter_preset import FilterPreset as FilterPresetModel
from grid.views.save_deal_view import SaveDealView
from api.filters import Filter, PresetFilter
from api.serializers import FilterPresetSerializer

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


class FilterView(APIView):

    def get_object(self):
        return self.request.session.get('filters', {})

    def post(self, request, *args, **kwargs):
        # TODO: make this a PATCH, and more RESTful.
        # TODO: use a serializer for param parsing
        stored_filters = self.get_object()

        # TODO: This works, but it's not very standard DRF.
        # Maybe convert to using the POST body for args in future?
        request_data = request.query_params.copy()
        request_data.update(request.data)

        action = request_data.get('action', 'nothing').lower()
        name = request_data.get('name', None)

        if action == 'set':
            if 'preset' in request_data:
                new_filter = PresetFilter(request_data['preset'], name=name)
            else:

                try:
                    variable = request_data['variable']
                    operator = request_data['operator']
                    value = request_data['value']
                except KeyError as err:
                    raise serializers.ValidationError(
                        {err.args[0]: _("This field is required.")})
                label = self._get_filter_label(variable)
                new_filter = Filter(
                    variable=variable, operator=operator, value=value,
                    label=label, name=name)

            stored_filters[new_filter.name] = new_filter
        elif action == 'remove':
            try:
                del stored_filters[name]
            except KeyError:
                pass

        request.session['filters'] = stored_filters

        return Response(stored_filters)

    @staticmethod
    def _get_filter_label(variable):
        # TODO: move label generation elsewhere, it shares code
        # with FilterViewMixin
        label = ''
        # for formsets, we want form.form
        deal_forms = [
            form.form if hasattr(form, 'form') else form
            for form in SaveDealView.FORMS
        ]
        for form in deal_forms:
            if variable in form.base_fields:
                label = str(form.base_fields[variable].label)
                break
        if not label and variable == 'activity_identifier':
            label = _('Deal ID')

        return label

    def get(self, request, *args, **kwargs):
        filters = self.get_object()

        return Response(filters)


class FilterPresetView(ListAPIView):
    '''
    The filter preset view returns a list of presets, filtered by group.
    If the show_groups query param is present, it instead returns a list of
    groups.
    '''
    serializer_class = FilterPresetSerializer

    def get_queryset(self):
        queryset = FilterPresetModel.objects.all()
        group_name = self.request.query_params.get('group', None)
        if group_name and 'show_groups' not in self.request.query_params:
            queryset = queryset.filter(group=group_name)

        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if 'show_groups' in request.query_params:
            groups = queryset.values_list('group', flat=True).distinct()
            response = Response(groups)
        else:
            serializer = self.get_serializer(queryset, many=True)
            response = Response(serializer.data)

        return response


class DashboardFilterView(APIView):

    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.session.get('dashboard_filters', {})

    def post(self, request, *args, **kwargs):
        '''
        TODO: use PATCH/DELETE here
        '''
        new_filters = {}

        request_data = request.query_params.copy()
        request_data.update(request.data)

        action = request_data.get('action', 'clear').lower()

        if action == 'set':
            if 'country' in request_data:
                new_filters['country'] = list(filter(lambda i: i, request_data.getlist('country')))
            elif 'region' in request_data:
                new_filters['region'] = list(filter(lambda i: i, request_data.getlist('region')))
            elif 'user' in request_data:
                new_filters['user'] = list(filter(lambda i: i, request_data.getlist('user')))

        self.request.session['dashboard_filters'] = new_filters

        return Response(new_filters)

    def get(self, request, *args, **kwargs):
        if 'clear' in request.query_params:
            filters = {}
            request.session['dashboard_filters'] = filters
        else:
            filters = self.get_object()

        return Response(filters)
