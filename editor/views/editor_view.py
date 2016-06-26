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
from api.query_sets.statistics_query_set import BASE_JOIN, BASE_CONDITION

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


class EditorView(TemplateView):

    template_name = 'dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return self.render_authenticated_user(request)
        else:
            return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

    def render_authenticated_user(self, request):
        csp = ChangesetProtocol()
        data = {
            "activities": ["updates", "deletes", "inserts"],
            "investors": ["deletes"],
        }
        request.POST = MultiValueDict({"data": [json.dumps(data)]})
        response = csp.dispatch(request, action="dashboard")
        response = json.loads(response.content.decode())
        public = get_public_deal_count()
        overall = get_overall_deal_count()
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


def get_overall_deal_count():
    return Activity.objects.filter(
        fk_status__name__in=('active', 'overwritten')
    ).values('activity_identifier').distinct().count()


def get_public_deal_count():
    from django.db import connection

    sql = """SELECT
    COUNT(DISTINCT a.activity_identifier) AS deals
FROM """ + Activity._meta.db_table + """ AS a,
(
    SELECT DISTINCT
        a.id
    FROM """ + Activity._meta.db_table + """ AS a
    """ + BASE_JOIN + """
    WHERE """ + BASE_CONDITION + """
    GROUP BY a.activity_identifier, a.id, pi.deal_size
) AS sub
WHERE a.id = sub.id
"""
    cursor = connection.cursor()
    cursor.execute(sql)
    result = cursor.fetchone()
    return result[0]



