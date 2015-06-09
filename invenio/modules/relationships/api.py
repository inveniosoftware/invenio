from werkzeug.utils import import_string

from .config import CFG_RELATIONSHIPS_NODE_ENGINE, CFG_RELATIONSHIPS_EDGE_ENGINE

Node = import_string(CFG_RELATIONSHIPS_NODE_ENGINE)
Edge = import_string(CFG_RELATIONSHIPS_EDGE_ENGINE)
