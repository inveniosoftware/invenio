from werkzeug import import_string

from .config import CFG_RELATIONSHIPS_EDGE_ENGINE

Edge = import_string(CFG_RELATIONSHIPS_EDGE_ENGINE)
