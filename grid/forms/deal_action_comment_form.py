from inspect import currentframe, getframeinfo

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.dateformat import DateFormat
from django.contrib.auth import get_user_model

from landmatrix.models.activity import Activity
from grid.fields import TitleField, UserModelChoiceField
from grid.widgets import CommentInput
from .base_form import BaseForm


class DealActionCommentForm(BaseForm):
    exclude_in_export = ("tg_action_comment", "source", "id", "assign_to_user", "tg_feedback_comment", "fully_updated")

    NOT_PUBLIC_REASON_CHOICES = (
        ("", _("---------")),
        (
            "Temporary removal from PI after criticism",
            _("Temporary removal from PI after criticism"),
        ),
        ("Research in progress", _("Research in progress")),
        ('Land Observatory Import (new)', _('Land Observatory Import (new)')),
        (
            'Land Observatory Import (duplicate)',
            _('Land Observatory Import (duplicate)'),
        ),
    )

    form_title = _('Action Comment')
    tg_action = TitleField(
        required=False, label="", initial=_("Action comment"))
    tg_action_comment = forms.CharField(
        required=True, label=_('Action comment'), widget=CommentInput)
    fully_updated = forms.BooleanField(
        required=False, label=_("Fully updated"))
    #fully_updated_history = forms.CharField(
    #    required=False, label=_("Fully updated history"),
    #    widget=forms.Textarea(attrs={"readonly":True, "cols": 80, "rows": 5}))


    tg_not_public = TitleField(
        required=False, label="", initial=_("Public deal"))
    not_public = forms.BooleanField(
        required=False, label=_("Not public"),
        help_text=_("Please specify in additional comment field"))
    not_public_reason = forms.ChoiceField(
        required=False, label=_("Reason"), choices=NOT_PUBLIC_REASON_CHOICES)
    tg_not_public_comment = forms.CharField(
        required=False, label=_("Comment on Not Public"), widget=CommentInput)

    tg_imported = TitleField(
        required=False, label="", initial=_("Import history"))
    source = forms.CharField(
        required=False, label=_("Import source"),
        widget=forms.TextInput(attrs={'readonly': True}))
    id = forms.CharField(
        required=False, label=_("Previous identifier"),
        widget=forms.TextInput(attrs={'size': '64', 'readonly': True}))

    tg_feedback = TitleField(required=False, label="", initial=_("Feedback"))
    assign_to_user = UserModelChoiceField(
        required=False, label=_("Assign to"), queryset=get_user_model().objects.none(),
        empty_label=_("Unassigned"))
    tg_feedback_comment = forms.CharField(
        required=False, label=_("Feedback comment"), widget=CommentInput)

    class Meta:
        name = 'action_comment'

    def __init__(self, *args, **kwargs):
        super(DealActionCommentForm, self).__init__(*args, **kwargs)
        self.fields['assign_to_user'].queryset = get_user_model().objects.filter(
            groups__name__in=("Editors", "Administrators")).order_by("username")

    def get_attributes(self, request=None):
        # Remove action comment, this field is handled separately in SaveDealView
        attributes = super(DealActionCommentForm, self).get_attributes(request)
        del attributes['tg_action_comment']
        return attributes

    @classmethod
    def get_data(cls, activity, group=None, prefix=""):
        # Remove action comment, due to an old bug it seems to exist as an attribute too
        data = super().get_data(activity, group, prefix)
        if 'tg_action_comment' in data:
            del data['tg_action_comment']

        return data