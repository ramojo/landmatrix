from django import forms
from django.utils.translation import ugettext_lazy as _

from landmatrix.models import BrowseCondition
from api.query_sets.sql_generation.filter_to_sql import FilterToSQL
from grid.views.base_model_form import BaseModelForm
from grid.views.browse_text_input import BrowseTextInput
from grid.views.browse_filter_conditions import get_field_by_key, a_keys
from grid.views.profiling_decorators import print_execution_time_and_num_queries

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


class BrowseConditionForm(BaseModelForm):

    variable = forms.ChoiceField(required=False, label=_("Variable"), initial="", choices=())
    operator = forms.ChoiceField(
        required=False, label=_("Operator"), initial="", choices=(), widget=forms.Select(attrs={"class": "operator"})
    )
    value = forms.CharField(required=False, label=_("Value"), initial="", widget=BrowseTextInput())

    @print_execution_time_and_num_queries
    def __init__(self, variables_activity=None, variables_investor=None, *args, **kwargs):
        super(BrowseConditionForm, self).__init__(*args, **kwargs)

        self._set_a_fields(variables_activity)
        self._set_sh_fields(variables_investor)

        self.fields["variable"].choices = self._variables()
        self.fields["operator"].choices = _operators()

    @print_execution_time_and_num_queries
    def _set_a_fields(self, variables_activity):
        if variables_activity:
            self.a_fields = [
                (str(key), get_field_by_key(str(key))) for key in a_keys().values() if key in variables_activity
            ]  # FIXME language
        else:
            self.a_fields = [(str(key), get_field_by_key(str(key))) for key in a_keys()]

    @print_execution_time_and_num_queries
    def _set_sh_fields(self, variables_investor):
        if variables_investor:
            self.sh_fields = [
                (str(key), get_field_by_key(str(key))) for key in a_keys().values() if key in variables_investor
            ]
        else:
            self.sh_fields = [(str(key), get_field_by_key(str(key))) for key in a_keys().values() if not key == 'name']

    def _variables(self):
        variables = [("", "-----"),
                     ("-1", "ID"),
                     ("-2", "Deal scope"),
                     ("fully_updated", "Fully updated"),
                     ("fully_updated_by", "Fully updated by"),
                     ("last_modification", "Last modification"),
                     ("inv_-2", "Primary investor")]
        variables.extend([(f[0], str(f[1].label)) for f in self.a_fields])
        variables.extend([(f[0], "Investor %s" % str(f[1].label)) for f in self.sh_fields])
        variables = sorted(variables, key=lambda x: x[1])
        return variables

    class Meta:

        model = BrowseCondition
        exclude = ('rule',)


def _operators():
    operators = [("", "-----")]
    operators.extend([(op, op_name[2]) for op, op_name in FilterToSQL.OPERATION_MAP.items()])
    return operators
