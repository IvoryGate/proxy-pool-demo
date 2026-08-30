"""RedisPool 测试。"""

import sys
import os
from unittest.mock import patch

import fakeredis

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.redis_client import RedisPool
from model.proxy import Proxy


def pool() -> RedisPool:
    """每次调用返回一个独立的 RedisPool，用 fakeredis 替代真实 Redis。"""
    fake = fakeredis.FakeRedis(decode_responses=True)

    p = RedisPool.__new__(RedisPool)
    p._redis = fake
    p._table = "test_proxy"
    p._table_https = "test_proxy:https"
    return p


def _make_proxy(
    addr: str = "1.2.3.4:8080",
    https: bool = False,
    fail_count: int = 0,
) -> Proxy:
    return Proxy(proxy=addr, https=https, fail_count=fail_count)


class TestPutAndGet:
    def test_put_then_get(self):
        """存一个代理，能取出来。"""
        p = pool()
        proxy = _make_proxy("1.2.3.4:8080")

        p.put(proxy)
        result = p.get()

        assert result is not None
        assert result.proxy == "1.2.3.4:8080"
        assert result.https is False

    def test_put_https_proxy(self):
        """存一个 https 代理，get(https=True) 能取到。"""
        p = pool()
        proxy = _make_proxy("1.2.3.4:443", https=True)

        p.put(proxy)

        assert p.get(https=True) is not None
        assert p.get(https=True).proxy == "1.2.3.4:443"

    def test_put_http_proxy_not_in_https_index(self):
        """存一个 http 代理，get(https=True) 取不到。"""
        p = pool()
        proxy = _make_proxy("1.2.3.4:8080", https=False)

        p.put(proxy)

        assert p.get(https=True) is None

    def test_update_proxy_changes_https_index(self):
        """更新代理的 https 状态，https 索引同步更新。

        注意：get(https=False) 实际上返回"任意代理"（代码行为），
        不是"只返回 http 代理"。
        """
        p = pool()
        proxy_http = _make_proxy("1.2.3.4:8080", https=False)
        p.put(proxy_http)

        # 改成 https
        proxy_https = _make_proxy("1.2.3.4:8080", https=True)
        p.put(proxy_https)

        # https 索引里有
        assert p.get(https=True) is not None
        # get(https=False) 也能取到（因为它取的是"任意"）
        assert p.get(https=False) is not None


class TestGet:
    def test_empty_pool(self):
        """空库 → None。"""
        p = pool()
        assert p.get() is None

    def test_empty_https_pool(self):
        """空库 → get(https=True) → None。"""
        p = pool()
        assert p.get(https=True) is None

    def test_get_https_skips_http_proxies(self):
        """https set 有脏数据（http 代理被误加入），跳过它们。"""
        p = pool()
        proxy_http = _make_proxy("1.2.3.4:8080", https=False)
        p.put(proxy_http)
        # 手动把 http 代理塞进 https set（模拟脏数据）
        p._redis.sadd(p._table_https, "1.2.3.4:8080")

        # get(https=True) 跳过该代理
        assert p.get(https=True) is None


class TestDelete:
    def test_delete_then_get_none(self):
        """删完取不到。"""
        p = pool()
        proxy = _make_proxy("1.2.3.4:8080")
        p.put(proxy)

        p.delete(proxy)

        assert p.get() is None

    def test_delete_removes_from_https_index(self):
        """删 https 代理，https 索引也清掉。"""
        p = pool()
        proxy = _make_proxy("1.2.3.4:443", https=True)
        p.put(proxy)

        p.delete(proxy)

        assert p.get(https=True) is None

    def test_delete_nonexistent(self):
        """删一个不存在的代理 → 不崩。"""
        p = pool()
        proxy = _make_proxy("1.2.3.4:8080")
        p.delete(proxy)  # 不抛异常即可


class TestCount:
    def test_count_empty(self):
        """空库 → total=0, https=0。"""
        p = pool()
        c = p.count()
        assert c["total"] == 0
        assert c["https"] == 0

    def test_count_after_puts(self):
        """存几个就报几个。"""
        p = pool()
        p.put(_make_proxy("1.2.3.4:8080"))
        p.put(_make_proxy("5.6.7.4:443", https=True))
        p.put(_make_proxy("9.8.7.6:3128"))

        c = p.count()
        assert c["total"] == 3
        assert c["https"] == 1


class TestGetAll:
    def test_get_all_empty(self):
        """空库 → 空列表。"""
        p = pool()
        assert p.getAll() == []

    def test_get_all(self):
        """存 3 个，取 3 个。"""
        p = pool()
        p.put(_make_proxy("1.2.3.4:8080"))
        p.put(_make_proxy("5.6.7.4:443"))
        p.put(_make_proxy("9.8.7.6:3128"))

        result = p.getAll()
        assert len(result) == 3
        addrs = {x.proxy for x in result}
        assert addrs == {"1.2.3.4:8080", "5.6.7.4:443", "9.8.7.6:3128"}


class TestGetProxy:
    def test_get_proxy_exists(self):
        """_get_proxy 存在的 key → 返回 Proxy。"""
        p = pool()
        proxy = _make_proxy("1.2.3.4:8080")
        p.put(proxy)

        result = p._get_proxy("1.2.3.4:8080")
        assert result is not None
        assert result.proxy == "1.2.3.4:8080"

    def test_get_proxy_not_exists(self):
        """_get_proxy 不存在的 key → None。"""
        p = pool()
        result = p._get_proxy("no-such-proxy")
        assert result is None


class TestRedisPoolInit:
    """构造函数测试。"""

    def test_default_params(self):
        """不传任何参数，走默认值。"""
        fake = fakeredis.FakeRedis(decode_responses=True)
        with patch("db.redis_client.redis.Redis", return_value=fake):
            p = RedisPool()
        assert p._table == "use_proxy"
        assert p._table_https == "use_proxy:https"

    def test_custom_params(self):
        """显式传参。"""
        fake = fakeredis.FakeRedis(decode_responses=True)
        with patch("db.redis_client.redis.Redis", return_value=fake):
            p = RedisPool(host="10.0.0.1", port=6380, db=5, table_name="my_proxy")
        assert p._table == "my_proxy"
        assert p._table_https == "my_proxy:https"

    def test_env_host_port(self):
        """从环境变量读 host/port。"""
        fake = fakeredis.FakeRedis(decode_responses=True)
        env = {"REDIS_HOST": "192.168.1.100", "REDIS_PORT": "6381"}
        with patch("db.redis_client.redis.Redis", return_value=fake), \
             patch.dict(os.environ, env):
            p = RedisPool()
        # 构造函数内部调用了 redis.Redis
        assert p._redis is fake
