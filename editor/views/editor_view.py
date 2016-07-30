from pprint import pprint

from django.shortcuts import redirect
from django.template.context import RequestContext
from django.conf import settings
from django.utils.datastructures import MultiValueDict
from django.views.generic import TemplateView
import json

from editor.views.changeset_protocol import ChangesetProtocol
from grid.views.view_aux_functions import render_to_response
from landmatrix.models.activity import Activity
from api.query_sets.statistics_query_set import PublicDealCountQuerySet


class EditorView(TemplateView):

    template_name = 'dashboard.html'

    def get(self, request):
        csp = ChangesetProtocol()
        data = {
            "activities": ["updates", "deletes", "inserts"],
            "investors": ["deletes"],
        }
        request.POST = MultiValueDict({"data": [json.dumps(data)]})
        response = csp.dispatch(request, action="dashboard")
        response = json.loads(response.content.decode())
        public = get_public_deal_count(request)
        overall = get_overall_deal_count(request)
        data = {
            "statistics": {
                "overall_deal_count": overall,
                "public_deal_count": public,
                "not_public_deal_count": overall-public
            },
            "view": "dashboard",
            "latest_added": response["latest_added"],
            "latest_modified": response["latest_modified"],
            "latest_deleted": response["latest_deleted"],
            "manage": response["manage"],
            "feedbacks": response["feedbacks"],
        }
        return render_to_response(self.template_name, data, RequestContext(request))


def get_overall_deal_count(request):
    return Activity.objects.filter(
        fk_status__name__in=('active', 'overwritten')
    ).values('activity_identifier').distinct().count()


def get_public_deal_count(request):
    qs = PublicDealCountQuerySet(request)
    return qs.all()[0][0]


class LogView(TemplateView):

    template_name = 'log.html'

    def get(self, request, action="latest_added"):
        csp = ChangesetProtocol()
        ACTION_MAP = {
            'latest_added': 'inserts',
            'latest_modified': 'updates',
            'latest_deleted': 'deletes',
        }
        data = {
            "activities": [ACTION_MAP.get(action)],
            "investors": [],
        }
        request.POST = MultiValueDict({"data": [json.dumps(data)]})
        request.GET = MultiValueDict({
            '%s_page'%action: request.GET.get("page", "1"),
            '%s_per_page'%action: ["50"],
        })
        response = csp.dispatch(request, action="dashboard")
        response = json.loads(response.content.decode())

        activities = response.get(action, [])
        data = {
            "view": "log",
            "action": action,
            "activities": activities['items'],
            "pagination": activities['pagination']
        }

        return render_to_response(self.template_name, data, context_instance=RequestContext(request))


