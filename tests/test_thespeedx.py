"""TheSpeedX 源测试。"""

import sys
import os
from unittest.mock import patch, MagicMock

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fetcher.sources.thespeedx import TheSpeedXHttpFetcher


def _make_response(text: str, status_code: int = 200) -> httpx.Response:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = text
    return resp


FAKE_RAW_TEXT = """1.2.3.4:8080
5.6.7.4:443
9.8.7.6:3128
"""


class TestTheSpeedXFetch:
    def test_normal_text(self):
        """正常文本，提取出 3 个代理。"""
        f = TheSpeedXHttpFetcher()
        fake_resp = _make_response(FAKE_RAW_TEXT)

        with patch.object(f, "_http_get", return_value=fake_resp) as mock_http:
            result = list(f.fetch())

        assert result == ["1.2.3.4:8080", "5.6.7.4:443", "9.8.7.6:3128"]
        mock_http.assert_called_once()

    def test_empty_response(self):
        """空响应 → 空列表。"""
        f = TheSpeedXHttpFetcher()
        fake_resp = _make_response("")

        with patch.object(f, "_http_get", return_value=fake_resp):
            result = list(f.fetch())

        assert result == []

    def test_network_failure(self):
        """_http_get 返回 None → 空列表，不崩。"""
        f = TheSpeedXHttpFetcher()

        with patch.object(f, "_http_get", return_value=None):
            result = list(f.fetch())

        assert result == []

    def test_deduplication(self):
        """有重复 → 去重。"""
        f = TheSpeedXHttpFetcher()
        fake_resp = _make_response("1.2.3.4:8080\n1.2.3.4:8080\n5.6.7.4:443")

        with patch.object(f, "_http_get", return_value=fake_resp):
            result = list(f.fetch())

        assert result == ["1.2.3.4:8080", "5.6.7.4:443"]

    def test_correct_url_called(self):
        """验证调用了正确的 raw URL。"""
        f = TheSpeedXHttpFetcher()
        fake_resp = _make_response("")

        with patch.object(f, "_http_get", return_value=fake_resp) as mock_http:
            list(f.fetch())

        called_url = mock_http.call_args[0][0]
        assert "raw.githubusercontent.com" in called_url
        assert "TheSpeedX" in called_url
