
from global_app.views.view_aux_functions import render_to_response

from django.views.generic.base import TemplateView
from django.template import RequestContext


class ChartView(TemplateView):
    template_name = "plugins/overview.html"

    def dispatch(self, request, *args, **kwargs):
        from random import randint
        print('B'+'O'*randint(1,9)+'AH ALDA!')
        context = {
            "view": "chart view",
        }
        return render_to_response(self.template_name, context, RequestContext(request))