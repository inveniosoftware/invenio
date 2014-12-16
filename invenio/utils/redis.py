from invenio.config import CFG_REDIS_HOSTS
if CFG_REDIS_HOSTS:
    from nydus.db import create_cluster


from invenio.config import CFG_REDIS_HOSTS

_REDIS_CONN = {}


class DummyRedisClient(object):
    def get(self, key):
        pass

    def set(self, key, value, timeout=None):
        pass

    def delete(self, key):
        pass


def get_redis(redis_namespace='default'):
    """Connects to a redis using nydus

    We simlulate a redis cluster by connecting to several redis servers
    in the background and using a consistent hashing ring to choose which
    server stores the data.
    Returns a redis object that can be used like a regular redis object
    see http://redis.io/
    """
    if not CFG_REDIS_HOSTS or not CFG_REDIS_HOSTS[redis_namespace]:
        return DummyRedisClient()

    redis = _REDIS_CONN.get(redis_namespace, None)
    if redis:
        return redis

    hosts_dict = {}
    for server_num, server_info in enumerate(CFG_REDIS_HOSTS[redis_namespace]):
        hosts_dict[server_num] = server_info

    redis = create_cluster({
        'backend': 'nydus.db.backends.redis.Redis',
        'router': 'nydus.db.routers.keyvalue.ConsistentHashingRouter',
        'hosts': hosts_dict
    })
    _REDIS_CONN[redis_namespace] = redis
    return redis
