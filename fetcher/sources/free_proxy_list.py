"""网页表格源：用 lxml xpath 从 HTML <table> 中抠出 ip:port。"""

from typing import Iterator, List, Set

from lxml import html

from fetcher.base import BaseFetcher


class FreeProxyListFetcher(BaseFetcher):
    name = "free-proxy-list"
    url = "https://free-proxy-list.net"

    def fetch(self) -> Iterator[str]:
        r = self._http_get(self.url, timeout=15)
        if r is None:
            return
        doc = html.fromstring(r.text)
        seen: Set[str] = set()
        for tr in doc.xpath("//table/tbody/tr[td]"):
            cells: List[str] = [
                td.text_content().strip() for td in tr.xpath("./td")
            ]
            if len(cells) < 2:
                continue
            ip, port = cells[0], cells[1]
            addr = f"{ip}:{port}"
            if addr not in seen:
                seen.add(addr)
                yield addr
