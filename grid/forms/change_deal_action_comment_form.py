__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

from grid.forms.add_deal_action_comment_form import AddDealActionCommentForm
from grid.widgets import TitleField, CommentInput

from django import forms
from django.utils.translation import ugettext_lazy as _


class ChangeDealActionCommentForm(AddDealActionCommentForm):

    tg_action = TitleField(required=False, label="", initial=_("Action comment"))
    tg_action_comment = forms.CharField(required=True, label="", widget=CommentInput)