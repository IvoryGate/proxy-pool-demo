"""FreeProxyList 源测试。"""

import sys
import os
from unittest.mock import patch, MagicMock

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fetcher.sources.free_proxy_list import FreeProxyListFetcher


def _make_response(text: str, status_code: int = 200) -> httpx.Response:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = text
    return resp


FAKE_HTML = """
<html><body>
<table>
  <thead><tr><th>IP Address</th><th>Port</th><th>Country</th></tr></thead>
  <tbody>
    <tr><td>1.2.3.4</td><td>8080</td><td>US</td></tr>
    <tr><td>5.6.7.4</td><td>443</td><td>DE</td></tr>
    <tr><td>9.8.7.6</td><td>3128</td><td>JP</td></tr>
  </tbody>
</table>
</body></html>
"""


class TestFreeProxyListFetch:
    def test_normal_html(self):
        """正常 HTML 表格，提取 3 个代理。"""
        f = FreeProxyListFetcher()
        fake_resp = _make_response(FAKE_HTML)

        with patch.object(f, "_http_get", return_value=fake_resp) as mock_http:
            result = list(f.fetch())

        assert result == ["1.2.3.4:8080", "5.6.7.4:443", "9.8.7.6:3128"]
        mock_http.assert_called_once()

    def test_empty_table(self):
        """表头有但 tbody 空 → 空列表。"""
        f = FreeProxyListFetcher()
        html_empty = """
        <html><body>
        <table>
          <thead><tr><th>IP</th><th>Port</th></tr></thead>
          <tbody></tbody>
        </table>
        </body></html>
        """
        fake_resp = _make_response(html_empty)

        with patch.object(f, "_http_get", return_value=fake_resp):
            result = list(f.fetch())

        assert result == []

    def test_deduplication(self):
        """有重复行 → 去重。"""
        f = FreeProxyListFetcher()
        html_dup = """
        <html><body>
        <table>
          <tbody>
            <tr><td>1.2.3.4</td><td>8080</td></tr>
            <tr><td>1.2.3.4</td><td>8080</td></tr>
            <tr><td>5.6.7.4</td><td>443</td></tr>
          </tbody>
        </table>
        </body></html>
        """
        fake_resp = _make_response(html_dup)

        with patch.object(f, "_http_get", return_value=fake_resp):
            result = list(f.fetch())

        assert result == ["1.2.3.4:8080", "5.6.7.4:443"]

    def test_malformed_rows(self):
        """某行不足 2 列 → 跳过，不崩。"""
        f = FreeProxyListFetcher()
        html_bad = """
        <html><body>
        <table>
          <tbody>
            <tr><td>1.2.3.4</td><td>8080</td></tr>
            <tr><td>only-one-cell</td></tr>
            <tr></tr>
          </tbody>
        </table>
        </body></html>
        """
        fake_resp = _make_response(html_bad)

        with patch.object(f, "_http_get", return_value=fake_resp):
            result = list(f.fetch())

        assert result == ["1.2.3.4:8080"]

    def test_network_failure(self):
        """_http_get 返回 None → 空列表。"""
        f = FreeProxyListFetcher()

        with patch.object(f, "_http_get", return_value=None):
            result = list(f.fetch())

        assert result == []
