"""Geonode 源测试。"""

import sys
import os
import json
from unittest.mock import patch, MagicMock

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fetcher.sources.geonode import GeonodeFetcher


def _make_json_response(data: dict, status_code: int = 200) -> httpx.Response:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = json.dumps(data)
    resp.json.return_value = data
    return resp


def _make_broken_json_response(status_code: int = 200) -> httpx.Response:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = "not json at all"
    resp.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
    return resp


FAKE_API_RESPONSE = {
    "data": [
        {"ip": "1.2.3.4", "port": "8080"},
        {"ip": "5.6.7.4", "port": "443"},
        {"ip": "9.8.7.6", "port": "3128"},
    ]
}


class TestGeonodeFetch:
    def test_normal_json(self):
        """正常 JSON，提取 3 个代理。"""
        f = GeonodeFetcher()
        fake_resp = _make_json_response(FAKE_API_RESPONSE)

        with patch.object(f, "_http_get", return_value=fake_resp) as mock_http:
            result = list(f.fetch())

        assert result == ["1.2.3.4:8080", "5.6.7.4:443", "9.8.7.6:3128"]
        mock_http.assert_called_once()

    def test_empty_data(self):
        """data 为空 → 空列表。"""
        f = GeonodeFetcher()
        fake_resp = _make_json_response({"data": []})

        with patch.object(f, "_http_get", return_value=fake_resp):
            result = list(f.fetch())

        assert result == []

    def test_missing_data_key(self):
        """JSON 没有 data 字段 → 空列表。"""
        f = GeonodeFetcher()
        fake_resp = _make_json_response({"something": "else"})

        with patch.object(f, "_http_get", return_value=fake_resp):
            result = list(f.fetch())

        assert result == []

    def test_invalid_json(self):
        """非法 JSON → .json() 抛异常 → 捕获 → 空列表。"""
        f = GeonodeFetcher()
        fake_resp = _make_broken_json_response()

        with patch.object(f, "_http_get", return_value=fake_resp):
            result = list(f.fetch())

        assert result == []

    def test_missing_ip_or_port(self):
        """JSON 中某条数据缺 ip 或 port → 跳过那条。"""
        f = GeonodeFetcher()
        bad_data = {
            "data": [
                {"ip": "1.2.3.4", "port": "8080"},   # 正常
                {"ip": "", "port": "443"},              # ip 为空 → 跳过
                {"ip": "9.8.7.6"},                      # 缺 port → 跳过
                {"port": "3128"},                       # 缺 ip → 跳过
            ]
        }
        fake_resp = _make_json_response(bad_data)

        with patch.object(f, "_http_get", return_value=fake_resp):
            result = list(f.fetch())

        assert result == ["1.2.3.4:8080"]

    def test_network_failure(self):
        """_http_get 返回 None → 空列表。"""
        f = GeonodeFetcher()

        with patch.object(f, "_http_get", return_value=None):
            result = list(f.fetch())

        assert result == []
