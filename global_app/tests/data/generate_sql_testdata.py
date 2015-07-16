__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

import os
from django.db import connection
from django.http import HttpRequest
import json

import os.path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


proj_path = os.path.join(os.path.dirname(__file__), "../..")
# This is so Django knows where to find stuff.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "landmatrix.settings")
sys.path.append(proj_path)

# This is so my local_settings.py gets loaded.
os.chdir(proj_path)

# This is so models get loaded.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from global_app.views import DummyActivityProtocol

def read_data(filename):
    with open(os.path.dirname(os.path.realpath(__file__)) + '/' + filename, 'r') as f:
        lines = f.readlines()
    parameters = eval(lines[1])
    return parameters['data'][0]

files_to_generate = [
    'by_crop',
    'by_data_source_type',
    'by_intention',
    'by_investor',
    'by_investor_country', 'by_investor_region', 'by_target_country', 'by_target_region', 'all_deals',
]

for filename in files_to_generate:
    postdata = read_data(filename+'.out')
    protocol = DummyActivityProtocol()
    request = HttpRequest()
    request.POST = {'data': postdata}
    res = protocol.dispatch(request, action="list_group").content
    print(res)
    open('/tmp/landmatrix_%s.out' % filename, 'a+').write(str(dict(request.POST))+"\n")
    open('/tmp/landmatrix_%s.out' % filename, 'a+').write(str(json.loads(res.decode('utf-8'))['activities'])+"\n")
