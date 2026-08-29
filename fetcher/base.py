"""代理源基类：定义所有代理源必须实现的统一接口。

子类只需实现 fetch()，yield 出 "ip:port" 字符串。
"""

from typing import Iterator, Optional

import httpx


class BaseFetcher:
    name: str = ""
    url: str = ""
    enabled: bool = True
    max_items: Optional[int] = None

    def __init__(self) -> None:
        self.proxy: Optional[str] = None

    def fetch(self) -> Iterator[str]:
        raise NotImplementedError

    def _http_get(
        self,
        url: str,
        timeout: int = 8,
        headers: Optional[dict] = None,
        **kwargs,
    ) -> Optional[httpx.Response]:
        try:
            if self.proxy:
                kwargs["proxy"] = f"http://{self.proxy}"
            return httpx.get(
                url,
                timeout=httpx.Timeout(
                    timeout,
                    connect=min(timeout, 5),
                    read=timeout,
                    pool=timeout,
                    write=timeout,
                ),
                follow_redirects=True,
                headers=headers or {},
                **kwargs,
            )
        except Exception:
            return None
