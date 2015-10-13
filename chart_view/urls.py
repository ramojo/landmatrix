__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

""" he `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import url, patterns
from .views import ChartView

urlpatterns = patterns('chartview.views',
    url(r'^$', ChartView.as_view(), name='app_main'),
    url(r'^all(?P<type>\.csv)?/$', ChartView.as_view(), name='all_charts'),

)