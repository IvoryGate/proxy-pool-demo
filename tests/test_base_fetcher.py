"""BaseFetcher 测试。"""

import sys
import os
from unittest.mock import patch, MagicMock

import httpx
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fetcher.base import BaseFetcher


def _make_response(status_code: int = 200, text: str = "") -> httpx.Response:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = text
    return resp


class TestHttpGet:
    """_http_get 测试。"""

    def test_success(self):
        """正常返回 200。"""
        fetcher = BaseFetcher()
        fake_resp = _make_response(200, "hello")

        with patch("httpx.get", return_value=fake_resp) as mock_get:
            result = fetcher._http_get("https://example.com")

        assert result is not None
        assert result.status_code == 200
        assert result.text == "hello"
        mock_get.assert_called_once()

    def test_http_error_still_returns_response(self):
        """对方返回 403/500 时，_http_get 依然返回 response。

        不检查状态码，调用方（子类）自己决定怎么处理。
        """
        fetcher = BaseFetcher()
        fake_resp = _make_response(403, "forbidden")

        with patch("httpx.get", return_value=fake_resp):
            result = fetcher._http_get("https://example.com")

        assert result is not None
        assert result.status_code == 403

    def test_network_exception_returns_none(self):
        """网络超时/连接失败 → 捕获异常，返回 None。"""
        fetcher = BaseFetcher()

        with patch("httpx.get", side_effect=httpx.ConnectError("timeout")):
            result = fetcher._http_get("https://example.com")

        assert result is None

    def test_with_proxy(self):
        """设置了 proxy 时，传给 httpx。"""
        fetcher = BaseFetcher()
        fetcher.proxy = "127.0.0.1:7890"
        fake_resp = _make_response(200, "ok")

        with patch("httpx.get", return_value=fake_resp) as mock_get:
            result = fetcher._http_get("https://example.com")

        assert result is not None
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["proxy"] == "http://127.0.0.1:7890"

    def test_timeout_passed(self):
        """自定义 timeout 被正确传递。"""
        fetcher = BaseFetcher()
        fake_resp = _make_response(200, "")

        with patch("httpx.get", return_value=fake_resp) as mock_get:
            fetcher._http_get("https://example.com", timeout=30)

        call_timeout = mock_get.call_args[1]["timeout"]
        assert call_timeout.read == 30


class TestBaseFetcherContract:
    """BaseFetcher 的契约测试。"""

    def test_fetch_raises(self):
        """直接调用基类 fetch() 应该抛 NotImplementedError。"""
        fetcher = BaseFetcher()
        with pytest.raises(NotImplementedError):
            fetcher.fetch()

    def test_default_attributes(self):
        """基类默认属性。"""
        fetcher = BaseFetcher()
        assert fetcher.proxy is None
        assert fetcher.name == ""
        assert fetcher.url == ""
        assert fetcher.enabled is True
        assert fetcher.max_items is None
