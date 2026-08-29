"""Checker 测试。

mock httpx.get，不走真实网络。
"""

import sys
import os
from unittest.mock import patch, MagicMock

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helper.check import Checker, PROXY_FORMAT, PROXY_IP_ONLY
from model.proxy import Proxy


def _make_response(status_code: int = 200, text: str = "") -> httpx.Response:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = text
    return resp


class TestProxyFormat:
    def test_valid_formats(self):
        """合法格式。"""
        assert PROXY_FORMAT.match("1.2.3.4:8080")
        assert PROXY_FORMAT.match("255.255.255.255:65535")
        assert PROXY_FORMAT.match("0.0.0.0:80")

    def test_invalid_formats(self):
        """非法格式。"""
        assert not PROXY_FORMAT.match("1.2.3.4")           # 没端口
        assert not PROXY_FORMAT.match("1.2.3.4:8080:9090")  # 多端口
        assert not PROXY_FORMAT.match("abc.def.ghi.jkl:80")  # 非数字IP
        assert not PROXY_FORMAT.match("1.2.3.4:5")          # 端口太短
        assert not PROXY_FORMAT.match("1.2.3.4:123456")     # 端口太长
        assert not PROXY_FORMAT.match("")                    # 空字符串


class TestProxyIpOnly:
    def test_valid_ip(self):
        """合法 IP。"""
        assert PROXY_IP_ONLY.match("1.2.3.4")
        assert PROXY_IP_ONLY.match("255.255.255.255")

    def test_invalid_ip(self):
        """非法 IP。"""
        assert not PROXY_IP_ONLY.match("1.2.3.4:8080")     # 带端口
        assert not PROXY_IP_ONLY.match("abc.def.ghi.jkl")   # 非数字
        assert not PROXY_IP_ONLY.match("")                   # 空字符串


class TestCheckerCheck:
    def test_invalid_format(self):
        """格式不合法 → 直接失败。"""
        c = Checker()
        proxy = Proxy(proxy="not-a-proxy")
        ok, fail_count = c.check(proxy)

        assert ok is False
        assert fail_count == 1
        assert proxy.last_status is False

    def test_valid_format_http_ok(self):
        """格式合法 + HTTP 验证通过 → 可用。"""
        c = Checker()
        proxy = Proxy(proxy="1.2.3.4:8080")

        with patch("helper.check.httpx.get") as mock_get:
            mock_get.return_value = _make_response(200, "1.2.3.4")
            ok, fail_count = c.check(proxy)

        assert ok is True
        assert fail_count == 0
        assert proxy.last_status is True

    def test_valid_format_http_fail(self):
        """格式合法 + HTTP 验证失败 → 不可用。"""
        c = Checker()
        proxy = Proxy(proxy="1.2.3.4:8080")

        with patch("helper.check.httpx.get") as mock_get:
            mock_get.side_effect = httpx.ConnectError("timeout")
            ok, fail_count = c.check(proxy)

        assert ok is False
        assert fail_count == 1
        assert proxy.last_status is False

    def test_hijacked_proxy(self):
        """HTTP 通过但返回内容不是纯 IP → 被劫持，标记为不可用。"""
        c = Checker()
        proxy = Proxy(proxy="1.2.3.4:8080")

        with patch("helper.check.httpx.get") as mock_get:
            mock_get.return_value = _make_response(200, "<html>广告页面</html>")
            ok, fail_count = c.check(proxy)

        assert ok is False
        assert fail_count == 1

    def test_https_detection(self):
        """HTTP 通过后自动检测 HTTPS 能力。"""
        c = Checker()
        proxy = Proxy(proxy="1.2.3.4:8080")

        with patch("helper.check.httpx.get") as mock_get:
            mock_get.return_value = _make_response(200, "1.2.3.4")
            ok, _ = c.check(proxy)

        assert proxy.https is True

    def test_http_status_code_not_200(self):
        """状态码不是 200 → 失败。"""
        c = Checker()
        proxy = Proxy(proxy="1.2.3.4:8080")

        with patch("helper.check.httpx.get") as mock_get:
            mock_get.return_value = _make_response(403, "forbidden")
            ok, fail_count = c.check(proxy)

        assert ok is False
        assert fail_count == 1


class TestCheckerFetchOk:
    def test_exception_returns_false(self):
        """网络异常 → False。"""
        c = Checker()
        with patch("helper.check.httpx.get") as mock_get:
            mock_get.side_effect = httpx.ConnectError("refused")
            assert c._fetch_ok("http://api.ipify.org", "1.2.3.4:8080") is False

    def test_empty_response(self):
        """空响应 → 匹配不了 IP → False。"""
        c = Checker()
        with patch("helper.check.httpx.get") as mock_get:
            mock_get.return_value = _make_response(200, "")
            assert c._fetch_ok("http://api.ipify.org", "1.2.3.4:8080") is False
