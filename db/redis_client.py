import os
import redis
from model.proxy import Proxy


class RedisPool:
    def __init__(self, host=None, port=None, db=0, table_name="use_proxy"):
        host = host or os.environ.get("REDIS_HOST", "127.0.0.1")
        port = int(port or os.environ.get("REDIS_PORT", 6379))
        self._redis = redis.Redis(host=host, port=port, db=db,
                                  decode_responses=True)
        self._table = table_name
        self._table_https = f"{table_name}:https"   # 索引：支持https的

    def put(self, proxy):
        """存一个代理，并同步维护各索引 set。"""
        self._redis.hset(self._table, proxy.proxy, proxy.to_json())
        if proxy.https:
            self._redis.sadd(self._table_https, proxy.proxy)
        else:
            self._redis.srem(self._table_https, proxy.proxy)

    def get(self, https=False):
        """按需取一个代理（不删除）。"""
        if https:
            members = self._redis.smembers(self._table_https)
        else:
            members = set(self._redis.hkeys(self._table))
        for pick in members:
            proxy = self._get_proxy(pick)
            if proxy and (not https or proxy.https):
                return proxy
        return None

    def delete(self, proxy):
        """删除一个代理（从所有索引同步移除）。"""
        self._redis.hdel(self._table, proxy.proxy)
        self._redis.srem(self._table_https, proxy.proxy)

    def count(self):
        return {"total": self._redis.hlen(self._table),
                "https": self._redis.scard(self._table_https)}

    def getAll(self):
        raw = self._redis.hgetall(self._table)
        return [Proxy.create_from_json(v) for v in raw.values()]

    def _get_proxy(self, proxy_str):
        raw = self._redis.hget(self._table, proxy_str)
        return raw and Proxy.create_from_json(raw)
