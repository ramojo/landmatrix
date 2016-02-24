__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

from grid.views.table_group_view import TableGroupView


class AllDealsView(TableGroupView):

    template_name = "all_deals.html"

    def dispatch(self, request, type='', *args, **kwargs):
        kwargs["group"] = "all%s" % (type and type or "")
        return super(AllDealsView, self).dispatch(request, *args, **kwargs)