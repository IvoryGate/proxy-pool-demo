"""JSON API 源：调用 geonode API，从 JSON 结构中提取 ip:port。"""

from typing import Iterator

import httpx

from fetcher.base import BaseFetcher


class GeonodeFetcher(BaseFetcher):
    name = "geonode"
    url = "https://geonode.com/"

    def fetch(self) -> Iterator[str]:
        api_url = (
            "https://proxylist.geonode.com/api/proxy-list?"
            "filterLastChecked=10&page=1&limit=100"
            "&sort_by=lastChecked&sort_type=desc"
        )
        r = self._http_get(api_url, timeout=15)
        if r is None:
            return
        try:
            data: list = r.json().get("data", [])
        except Exception:
            return
        for item in data:
            ip: str = item.get("ip", "")
            port: str = item.get("port", "")
            if ip and port:
                yield f"{ip}:{port}"
