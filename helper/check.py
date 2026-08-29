"""验证器：格式校验 + 存活验证。

两刀：第一刀砍格式不合法的，第二刀砍连不上或被劫持的。
"""

import re
from typing import Tuple

import httpx

from model.proxy import Proxy

PROXY_FORMAT: re.Pattern = re.compile(
    r"^\d{1,3}(?:\.\d{1,3}){3}:\d{2,5}$"
)
PROXY_IP_ONLY: re.Pattern = re.compile(
    r"^\d{1,3}(?:\.\d{1,3}){3}$"
)

TIMEOUT: int = 3
HTTP_URL: str = "http://api.ipify.org"
HTTPS_URL: str = "https://api.ipify.org"


class Checker:
    def __init__(self, timeout: int = TIMEOUT) -> None:
        self.timeout = httpx.Timeout(
            timeout,
            connect=min(timeout, 2),
            read=timeout,
            pool=timeout,
            write=timeout,
        )

    def check(self, proxy: Proxy) -> Tuple[bool, int]:
        """验证一个 proxy，更新其状态。返回 (是否可用, fail_count)。"""
        if not PROXY_FORMAT.match(proxy.proxy):
            proxy.fail_count += 1
            proxy.last_status = False
            return False, proxy.fail_count

        http_ok = self._fetch_ok(HTTP_URL, proxy.proxy)
        if http_ok:
            proxy.https = self._fetch_ok(HTTPS_URL, proxy.proxy)
            proxy.fail_count = 0
            proxy.last_status = True
        else:
            proxy.fail_count += 1
            proxy.last_status = False
        return http_ok, proxy.fail_count

    def _fetch_ok(self, url: str, proxy_addr: str) -> bool:
        try:
            r = httpx.get(
                url,
                proxy=f"http://{proxy_addr}",
                timeout=self.timeout,
                verify=False,
            )
            if r.status_code != 200:
                return False
            return bool(PROXY_IP_ONLY.match(r.text.strip()))
        except Exception:
            return False
