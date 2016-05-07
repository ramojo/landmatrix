from django.conf.urls import url, patterns
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie

from grid.views import *

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

CACHE_TIMEOUT = 24*3600

urlpatterns = patterns('grid.views',
    # please leave them here, commented out, for quick cache de-/activation when developing
    # url(r'^$', AllDealsView.as_view(), name='app_main'),
    # url(r'^(?P<group>.+)/(?P<list>.+)/$', TableGroupView.as_view(), name='table_list'),

    url(
        r'^$',
        vary_on_cookie(cache_page(CACHE_TIMEOUT)(AllDealsView.as_view())),
        name='data'
    ),
    url(
        r'^all\.(?P<format>(csv|xml|xls))/$',
        vary_on_cookie(cache_page(CACHE_TIMEOUT)(AllDealsExportView.as_view())),
        name='export'
    ),
    url(
        r'^deal/(?P<deal_id>[\d]+)\.(?P<format>(csv|xml|xls))/$',
        vary_on_cookie(cache_page(CACHE_TIMEOUT)(DealDetailExportView.as_view())),
        name='export'
    ),
    url(
        r'^(?P<group>.+)/(?P<list>.+)\.(?P<format>(csv|xml|xls))/$',
        vary_on_cookie(cache_page(CACHE_TIMEOUT)(TableGroupExportView.as_view())),
        name='export'
    ),
    url(
        r'^(?P<group>.+)\.(?P<format>(csv|xml|xls))/$',
        vary_on_cookie(cache_page(CACHE_TIMEOUT)(TableGroupExportView.as_view())),
        name='export'
    ),

    # needs to come last, regexp catches all expressions
    url(
        r'^(?P<group>.+)/(?P<group_value>.+)/$',
        vary_on_cookie(cache_page(CACHE_TIMEOUT)(TableGroupView.as_view())),
        name='table_list'
    ),
    url(
        r'^(?P<group>.+)/$',
        vary_on_cookie(cache_page(CACHE_TIMEOUT)(TableGroupView.as_view())),
        name='table_list'
    ),
)
