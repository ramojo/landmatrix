from grid.forms.deal_employment_form import DealEmploymentForm
from grid.forms.deal_general_form import DealGeneralForm
from grid.forms.deal_overall_comment_form import DealOverallCommentForm
from grid.forms.deal_action_comment_form import DealActionCommentForm
from grid.forms.deal_contract_form import DealContractFormSet
from grid.forms.deal_data_source_form import AddDealDataSourceFormSet
from grid.forms.deal_former_use_form import DealFormerUseForm
from grid.forms.deal_gender_related_info_form import DealGenderRelatedInfoForm
from grid.forms.deal_local_communities_form import DealLocalCommunitiesForm
from grid.forms.deal_produce_info_form import DealProduceInfoForm
from grid.forms.deal_spatial_form import DealSpatialFormSet
from grid.forms.deal_water_form import DealWaterForm
from grid.forms.deal_vggt_form import DealVGGTForm
from grid.forms.operational_stakeholder_form import OperationalStakeholderForm

from landmatrix.models.activity_attribute_group import ActivityAttribute, \
    HistoricalActivityAttribute, ActivityAttributeGroup
from landmatrix.models.activity import Activity
from landmatrix.models.investor import InvestorActivityInvolvement
from landmatrix.models.language import Language
from landmatrix.models.status import Status

from django.views.generic import TemplateView

from django.db import transaction
from django.contrib import messages
from django.core.exceptions import MultipleObjectsReturned
from django.utils.translation import ugettext_lazy as _

from datetime import date, datetime

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


class SaveDealView(TemplateView):
    FORMS = [
        DealSpatialFormSet,
        DealGeneralForm,
        DealContractFormSet,
        DealEmploymentForm,
        OperationalStakeholderForm,
        AddDealDataSourceFormSet,
        DealLocalCommunitiesForm,
        DealFormerUseForm,
        DealProduceInfoForm,
        DealWaterForm,
        DealGenderRelatedInfoForm,
        DealVGGTForm,
        DealOverallCommentForm,
        DealActionCommentForm,
    ]
    deal_id = None
    success_message = _('Your changes to the deal have been submitted successfully. The changes will be reviewed and published soon.')
    success_message_admin = _('Your changes to the deal have been saved successfully.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**self.kwargs)
        if self.request.method != 'POST':
            context['forms'] = self.get_forms()
        context['kwargs'] = self.kwargs
        return context

    def get_forms(self, data=None, files=None):
        raise NotImplementedError("get_forms must be implemented in "
                                  "subclasses.")

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        forms = self.get_forms(self.request.POST, files=self.request.FILES)
        if all(form.is_valid() for form in forms):
            return self.form_valid(forms)
        else:
            return self.form_invalid(forms)

    def form_valid(self, forms):
        hactivity = self.get_object()
        investor_form = list(filter(lambda f: isinstance(f, OperationalStakeholderForm), forms))[0]
        # Create new historical activity
        hactivity.pk = None
        hactivity.history_user = self.request.user
        hactivity.history_date = datetime.now()
        hactivity.save()
        # Create new activity attributes
        action_comment = self.create_attributes(hactivity, forms)
        hactivity.update_public_activity()
        self.create_involvement(hactivity, investor_form)
        if self.request.user.has_perm('landmatrix.change_activity'):
            messages.success(self.request, self.success_message_admin.format(self.deal_id))
        else:
            # Create changeset (for review)
            changeset = ActivityChangeset.objects.create(
                fk_activity=hactivity,
                comment=action_comment
            )
            messages.success(self.request, self.success_message.format(self.deal_id))

        context = self.get_context_data(**self.kwargs)
        context['forms'] = forms
        return self.render_to_response(context)


    def form_invalid(self, forms):
        messages.error(self.request, _('Please correct the error below.'))

        context = self.get_context_data(**self.kwargs)
        context['forms'] = forms
        return self.render_to_response(context)

    def create_attributes(self, activity, forms):
        action_comment = ''
        # Create new attributes
        for form in forms:
            attributes = form.get_attributes(self.request)
            if not attributes:
                continue
            # Formset?
            if isinstance(attributes, list):
                for count, form_attributes in enumerate(attributes):
                    if form_attributes:
                        aag, created = ActivityAttributeGroup.objects.get_or_create(
                            name='%s_%i' % (form.Meta.name, count),
                        )
                        for name, kwargs in form_attributes.items():
                            kwargs.update({
                                'name': name,
                                'fk_activity': activity,
                                'fk_group': aag,
                                'fk_language_id': 1,
                            })
                            aa = HistoricalActivityAttribute.objects.create(**kwargs)
            # Form
            elif attributes:
                aag, created = ActivityAttributeGroup.objects.get_or_create(
                    name=form.Meta.name
                )
                for name, kwargs in attributes.items():
                    kwargs.update({
                        'name': name,
                        'fk_activity': activity,
                        'fk_group': aag,
                        'fk_language_id': 1,
                    })
                    aa = HistoricalActivityAttribute.objects.create(**kwargs)

            if form.Meta.name == 'action_comment':
                action_comment = form.cleaned_data['tg_action_comment']

        return action_comment

    def create_involvement(self, activity, form):
        # FIXME
        # Problem here: Involvements are not historical yet, but activity and investors are.
        # As an intermediate solution we'll just create another involvement which links
        # to the public activity, which will replace the current involvement when the
        # historical activity gets approved.
        activity = Activity.objects.get(activity_identifier=activity.activity_identifier)

        operational_stakeholder = form.cleaned_data['operational_stakeholder']
        # Update operational stakeholder (involvement)
        #involvements = InvestorActivityInvolvement.objects.filter(fk_activity=activity)
        #if len(involvements) > 1:
        #    raise MultipleObjectsReturned(
        #        'More than one operational stakeholder for activity %s' % str(self.get_object())
        #    )
        #elif len(involvements):
        #    involvement = involvements.last()
        #    involvement.fk_investor = operational_stakeholder
        #else:
        involvement = InvestorActivityInvolvement.objects.create(
            fk_activity=activity,
            fk_investor=operational_stakeholder,
            fk_status_id=activity.STATUS_PENDING,
        )
        involvement.save()

