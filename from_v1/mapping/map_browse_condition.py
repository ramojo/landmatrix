from mapping.map_model import MapModel
import landmatrix.models
import old_editor.models
from mapping.map_browse_rule import MapBrowseRule

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


class MapBrowseCondition(MapModel):
    old_class = old_editor.models.BrowseCondition
    new_class = landmatrix.models.BrowseCondition
    depends = [ MapBrowseRule ]
