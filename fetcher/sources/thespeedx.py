"""GitHub 纯文本列表源：每行一个 ip:port，正则提取。"""

from typing import Iterator

from fetcher.base import BaseFetcher
from fetcher.util import parse_proxies_from_text, yield_unique_proxies


class TheSpeedXHttpFetcher(BaseFetcher):
    name = "thespeedx-http"
    url = "https://github.com/TheSpeedX/PROXY-List"

    def fetch(self) -> Iterator[str]:
        raw_url = (
            "https://raw.githubusercontent.com/TheSpeedX/"
            "PROXY-List/master/http.txt"
        )
        r = self._http_get(raw_url, timeout=15)
        if r is None:
            return
        yield from yield_unique_proxies(parse_proxies_from_text(r.text))
