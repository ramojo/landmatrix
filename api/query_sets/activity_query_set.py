import json
from pprint import pprint

from api.query_sets.sql_generation.record_reader import RecordReader
from grid.views.view_aux_functions import apply_filters_from_session
from grid.views.profiling_decorators import print_execution_time_and_num_queries

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


class ActivityQuerySet:

    DEBUG = True

    def __init__(self, request):
        data = request.POST.get('data', '{"filters": {}, "columns": {}, "status": {}}')
        self.data = json.loads(data)
        apply_filters_from_session(request, self.data['filters'])
        self.is_staff = request.user.is_staff
        if self.DEBUG: pprint(self.data['filters'], width=120, compact=True)
        if 'columns' not in self.data:
            self.data['columns'] = {}

    @print_execution_time_and_num_queries
    def all(self):
        # if filters.get('group_value') == '':
        reader = RecordReader(self.data["filters"], self.data["columns"], self.data["status"], is_staff=self.is_staff)
        if self.DEBUG:
            print(reader.get_all_sql())
        activities = reader.get_all(assemble=reader._make_padded_record_from_column_data)
        return {
            "errors": [],
            "activities": activities,
        }


