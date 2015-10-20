from global_app.forms.base_form import BaseForm
from landmatrix.models.country import Country
from landmatrix.models.involvement import Involvement
from landmatrix.models.stakeholder_attribute_group import StakeholderAttributeGroup

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

from global_app.forms.deal_secondary_investor_form import DealSecondaryInvestorForm

from django.forms.formsets import formset_factory

from copy import copy


BaseDealSecondaryInvestorFormSet = formset_factory(DealSecondaryInvestorForm, extra=0)


class DealSecondaryInvestorFormSet(BaseDealSecondaryInvestorFormSet):
    def get_taggroups(self, request=None):
        return []

    def get_stakeholders(self):
        stakeholders = []
        for i, form in enumerate(self.forms):
            stakeholder = {}
            for j, taggroup in enumerate(form.get_taggroups()):
                comment = taggroup.get("comment", "")
                for i, t in reversed(list(enumerate(taggroup["tags"]))):
                    if t["key"] == "investor":
                        # Existing investor
                        stakeholder["investment_ratio"] = str(taggroup["investment_ratio"])
                        stakeholder["id"] = t["value"]
                        stakeholder["taggroups"] = [{
                            "main_tag": {"key": "name", "value": "General"},
                            "comment": comment,
                        }]
                if not stakeholder:
                    stakeholder["investment_ratio"] = taggroup["investment_ratio"]
                    stakeholder["taggroups"] = [{
                        "main_tag": {"key": "name", "value": "General"},
                        "tags": taggroup["tags"],
                        "comment": comment,
                    }]
            if stakeholder:
                stakeholders.append(copy(stakeholder))
        return stakeholders


    @classmethod
    def get_data(cls, deal):
        from inspect import currentframe, getframeinfo

        #raise IOError, [{"investor": str(i.fk_stakeholder.id)} for i in activity.involvement_set.all()]
        data = []
        involvements = deal.involvement_set().all() #get_involvements_for_activity(activity)
        for i, involvement in enumerate(involvements):
            if not involvement.fk_stakeholder:
                continue

            if False:
                comments = Comment.objects.filter(fk_sh_tag_group__fk_stakeholder=involvement.fk_stakeholder.id, fk_sh_tag_group__fk_sh_tag__fk_sh_value__value="General", fk_sh_tag_group__fk_sh_tag__fk_sh_key__key="name").order_by("-id")
            else:
                frameinfo = getframeinfo(currentframe())
                print('*** comments not yet implemented! ',frameinfo.filename, frameinfo.lineno)
                comments = None

            comment = comments[0].comment if comments and len(comments) > 0 else ''
            investor = {
                "investor": involvement.fk_stakeholder.id,
                "tg_general_comment": comment,
                "investment_ratio": involvement.investment_ratio,
            }
            data.append(investor)

        return data


def get_investors(deal):
    return {
        'primary_investor': get_primary_investor(deal),
        'secondary_investors': get_secondary_investors(deal)
    }


def get_primary_investor(deal):
    return deal.primary_investor


def get_secondary_investors(deal):
    stakeholders = [
        {
            'investment_ratio': Involvement.objects.filter(fk_stakeholder=sh).first().investment_ratio,
            'tags': {key: resolve_country(key, value)
                     for key, value in StakeholderAttributeGroup.objects.filter(fk_stakeholder=sh).first().attributes.items()}
        } for sh in deal.stakeholders
    ]
    return stakeholders


def resolve_country(key, value):
    if key != 'country': return value
    if not value.isdigit(): return value
    return Country.objects.get(id=value).name