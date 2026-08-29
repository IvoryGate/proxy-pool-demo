"""fetcher 通用工具：正则提取、去重。

用到的源自己 import，不污染 BaseFetcher 的接口契约。
"""

import re
from typing import Iterator, List

PROXY_PATTERN: re.Pattern = re.compile(
    r"(?<![\d.])(\d{1,3}(?:\.\d{1,3}){3})"
    r"(?:\s*:\s*|\s+)"
    r"(\d{2,5})(?!\d)"
)


def parse_proxies_from_text(text: str) -> List[str]:
    """从文本中正则抠出所有 "ip:port"。"""
    if not text:
        return []
    return [
        f"{ip}:{port}"
        for ip, port in PROXY_PATTERN.findall(text)
    ]


def yield_unique_proxies(proxies: List[str]) -> Iterator[str]:
    """去重后逐个 yield。"""
    seen: set = set()
    for proxy in proxies:
        if proxy not in seen:
            seen.add(proxy)
            yield proxy
