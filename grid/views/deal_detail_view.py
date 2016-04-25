from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponse
from django.db.models import Max
from django.views.generic import TemplateView
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

from landmatrix.models import Deal
from landmatrix.models.activity import Activity
from landmatrix.models.country import Country
from landmatrix.models.deal_history import DealHistoryItem
from landmatrix.pdfgen import PDFViewMixin

from grid.forms.change_deal_employment_form import ChangeDealEmploymentForm
from grid.forms.change_deal_general_form import ChangeDealGeneralForm
from grid.forms.deal_data_source_form import (
    PublicViewDealDataSourceFormSet, DealDataSourceForm,
)
from grid.forms.deal_former_use_form import DealFormerUseForm
from grid.forms.deal_gender_related_info_form import DealGenderRelatedInfoForm
from grid.forms.deal_local_communities_form import DealLocalCommunitiesForm
from grid.forms.deal_produce_info_form import PublicViewDealProduceInfoForm
from grid.forms.deal_spatial_form import PublicViewDealSpatialForm
from grid.forms.deal_water_form import DealWaterForm
from grid.forms.operational_stakeholder_form import OperationalStakeholderForm
from grid.views.view_aux_functions import render_to_string, render_to_response
from grid.forms.country_specific_forms import get_country_specific_form_class


__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


FORMS = [
    ("spatial_data", PublicViewDealSpatialForm),
    ("general_information", ChangeDealGeneralForm),
    ("employment", ChangeDealEmploymentForm),
    ("investor_info", OperationalStakeholderForm),
    ("data_sources", PublicViewDealDataSourceFormSet),
    ("local_communities", DealLocalCommunitiesForm),
    ("former_use", DealFormerUseForm),
    ("produce_info", PublicViewDealProduceInfoForm),
    ("water", DealWaterForm),
    ("gender-related_info", DealGenderRelatedInfoForm),
]


class DealDetailView(PDFViewMixin, TemplateView):

    template_name = 'deal-detail.html'
    pdf_export_url = 'deal_detail_pdf'
    pdf_render_url = 'deal_detail'

    def get_pdf_filename(self, request, *args, **kwargs):
        return 'deal_{deal_id}.pdf'.format(**kwargs)

    def get_context_data(self, deal_id):
        try:
            if '_' in deal_id:
                deal = deal_from_activity_id_and_timestamp(deal_id)
            else:
                deal = get_latest_valid_deal(deal_id)
        except ObjectDoesNotExist as e:
            return HttpResponse('Deal {} does not exist ({})'.format(deal_id, e), status=404)

        context = super(DealDetailView, self).get_context_data()
        context['deal'] = {
            'id': deal.activity.id,
            'activity': deal.activity,
            'activity_identifier': deal.activity.activity_identifier,
            'attributes': deal.attributes,
            'operational_stakeholder': deal.operational_stakeholder,
            'stakeholders': deal.stakeholders,
            'object': deal
        }
        context['forms'] = get_forms(deal)
        context['investor'] = deal.stakeholders
        try:
            context['history'] = DealHistoryItem.get_history_for(deal)
        except AttributeError:
            pass

        context['export_formats'] = ("XML", "CSV", "XLS", "PDF",)

        return context

    def render_forms(self, request, context):
        return render_to_response(self.template_name, context, RequestContext(request))

    def render_forms_to_string(self, request, context):
        return render_to_string(self.template_name, context, RequestContext(request))


def get_latest_valid_deal(deal_id):
    deal = Deal(deal_id)

    if deal.activity.fk_status.name in ['active', 'overwritten']:
        return deal
    elif deal.activity.fk_status.name in ['deleted', 'to_delete']:
        raise ObjectDoesNotExist('Deal {} is deleted or waiting for deletion'.format(deal_id))

    for timestamp, item in DealHistoryItem.get_history_for(deal).items():
        if item.activity.fk_status.name in ['active', 'overwritten']:
            print('active:', timestamp)
            return item
        else:
            print('inactive', timestamp)

    raise ObjectDoesNotExist('No approved version found for deal {}'.format(deal_id))


def display_valid_forms(forms):
    activity_identifier = Activity.objects.values().aggregate(Max('activity_identifier'))[
                              'activity_identifier__max'] + 1
    activity = Activity(activity_identifier=activity_identifier, fk_status_id=1, version=1)
    for form in forms:
        if form.Meta.name == 'investor_info':
            print('investor_info', form.cleaned_data)
        elif form.Meta.name == 'data_sources':
            for sub_form_data in form.cleaned_data:
                if sub_form_data['type'] and isinstance(sub_form_data['type'], int):
                    field = DealDataSourceForm().fields['type']
                    choices = dict(field.choices)
                    sub_form_data['type'] = str(choices[sub_form_data['type']])
                group = create_attribute_group(activity, sub_form_data)
                print(form.Meta.name, group)
        elif form.Meta.name == 'spatial_data':
            for sub_form_data in form.cleaned_data:
                if sub_form_data['target_country'] and isinstance(sub_form_data['target_country'], Country):
                    sub_form_data['target_country'] = sub_form_data['target_country'].pk
                group = create_attribute_group(activity, sub_form_data)
                print(form.Meta.name, group)
        else:
            if any(form.cleaned_data.values()):
                group = create_attribute_group(activity, form.cleaned_data)
                print(form.Meta.name, group)
            else:
                print('no data sent:', form.Meta.name)


def display_invalid_forms(forms):
    for form in forms:
        if form.is_valid():
            print(form.__class__.__name__, form.cleaned_data)
        else:
            print(form.__class__.__name__, 'INVALID:', form.errors)


def get_forms(deal):
    forms = [get_form(deal, form) for form in FORMS]

    country_specific_form_class = get_country_specific_form_class(deal)
    if country_specific_form_class:
        country_specific_form_class_tuple = (
            country_specific_form_class.Meta.name, country_specific_form_class,
        )
        country_specific_form = get_form(deal,
                                         country_specific_form_class_tuple)
        forms.append(country_specific_form)

    return forms


def get_form(deal, form_class):
    data = form_class[1].get_data(deal)
    return form_class[1](initial=data)


def deal_from_activity_id_and_timestamp(id_and_timestamp):
    from datetime import datetime
    from dateutil.tz import tzlocal
    if '_' in id_and_timestamp:
        activity_identifier, timestamp = id_and_timestamp.split('_')

        activity = Activity.objects.filter(activity_identifier=activity_identifier).order_by('id').last()
        if activity is None:
            raise ObjectDoesNotExist('activity_identifier %s' % activity_identifier)

        history = activity.history.filter(history_date__lte=datetime.fromtimestamp(float(timestamp), tz=tzlocal())).\
            filter(fk_status_id__in=(2, 3)).last()
        if history is None:
            raise ObjectDoesNotExist('Public deal with activity_identifier %s as of timestamp %s' % (activity_identifier, timestamp))

        return DealHistoryItem.from_activity_with_date(history, datetime.fromtimestamp(float(timestamp), tz=tzlocal()))

    raise RuntimeError('should contain _ separating activity id and timestamp: ' + id_and_timestamp)
