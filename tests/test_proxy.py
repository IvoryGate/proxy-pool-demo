"""Proxy 数据模型测试。"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model.proxy import Proxy


class TestProxyInit:
    """Proxy 构造函数测试。"""

    def test_minimal_args(self):
        """只传 proxy，其他全走默认值。"""
        p = Proxy(proxy="1.2.3.4:8080")
        assert p.proxy == "1.2.3.4:8080"
        assert p.https is False
        assert p.fail_count == 0
        assert p.check_count == 0
        assert p.last_status is False
        assert p.last_time is None

    def test_all_args(self):
        """全部参数显式传入。"""
        p = Proxy(
            proxy="5.6.7.4:443",
            https=True,
            fail_count=3,
            check_count=10,
            last_status=True,
            last_time="2026-08-29",
        )
        assert p.proxy == "5.6.7.4:443"
        assert p.https is True
        assert p.fail_count == 3
        assert p.check_count == 10
        assert p.last_status is True
        assert p.last_time == "2026-08-29"


class TestProxyJson:
    """to_json / create_from_json 序列化往返测试。"""

    def test_round_trip(self):
        """序列化再反序列化，字段值不变。"""
        original = Proxy(
            proxy="1.2.3.4:8080",
            https=True,
            fail_count=2,
            check_count=5,
            last_status=True,
            last_time="2026-08-29",
        )
        json_str = original.to_json()
        restored = Proxy.create_from_json(json_str)

        assert restored.proxy == original.proxy
        assert restored.https == original.https
        assert restored.fail_count == original.fail_count
        assert restored.check_count == original.check_count
        assert restored.last_status == original.last_status
        assert restored.last_time == original.last_time

    def test_create_from_json_missing_fields(self):
        """老版本 JSON 缺字段时，用默认值兜底（向后兼容）。"""
        # 模拟老版本只存了 proxy 和 https
        old_json = '{"proxy": "1.2.3.4:8080", "https": true}'
        p = Proxy.create_from_json(old_json)

        assert p.proxy == "1.2.3.4:8080"
        assert p.https is True
        assert p.fail_count == 0      # 缺字段 → 默认值
        assert p.check_count == 0
        assert p.last_status is False
        assert p.last_time is None

    def test_create_from_json_empty(self):
        """完全空的 JSON。"""
        p = Proxy.create_from_json("{}")
        assert p.proxy == ""          # 默认值
        assert p.https is False
