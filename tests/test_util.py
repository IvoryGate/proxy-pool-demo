"""fetcher/util.py 工具函数测试。"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fetcher.util import parse_proxies_from_text, yield_unique_proxies


class TestParseProxiesFromText:
    """正则提取 ip:port 测试。"""

    def test_normal_text(self):
        """标准格式：每行一个 ip:port。"""
        text = "1.2.3.4:8080\n5.6.7.4:443\n9.8.7.6:3128"
        result = parse_proxies_from_text(text)
        assert result == ["1.2.3.4:8080", "5.6.7.4:443", "9.8.7.6:3128"]

    def test_space_separator(self):
        """ip 和 port 之间用空格分隔（不是冒号）。"""
        text = "1.2.3.4 8080\n5.6.7.4  443"
        result = parse_proxies_from_text(text)
        assert result == ["1.2.3.4:8080", "5.6.7.4:443"]

    def test_mixed_with_junk(self):
        """代理混在垃圾文本里。"""
        text = "some header line\n1.2.3.4:8080\nanother line\n5.6.7.4:443\nend"
        result = parse_proxies_from_text(text)
        assert result == ["1.2.3.4:8080", "5.6.7.4:443"]

    def test_empty_string(self):
        """空字符串 → 空列表。"""
        assert parse_proxies_from_text("") == []

    def test_none_equivalent(self):
        """None（实际传入 ""）→ 空列表。"""
        assert parse_proxies_from_text("") == []

    def test_no_proxies(self):
        """纯文本不含任何代理。"""
        text = "hello world this is just text"
        assert parse_proxies_from_text(text) == []

    def test_port_boundary(self):
        """端口号边界：2位和5位。"""
        text = "1.2.3.4:80\n5.6.7.4:65535"
        result = parse_proxies_from_text(text)
        assert result == ["1.2.3.4:80", "5.6.7.4:65535"]


class TestYieldUniqueProxies:
    """去重 yield 测试。"""

    def test_no_duplicates(self):
        """无重复 → 原样输出。"""
        proxies = ["1.2.3.4:8080", "5.6.7.4:443"]
        result = list(yield_unique_proxies(proxies))
        assert result == ["1.2.3.4:8080", "5.6.7.4:443"]

    def test_with_duplicates(self):
        """有重复 → 去重，保留第一次出现的顺序。"""
        proxies = ["1.2.3.4:8080", "5.6.7.4:443", "1.2.3.4:8080"]
        result = list(yield_unique_proxies(proxies))
        assert result == ["1.2.3.4:8080", "5.6.7.4:443"]

    def test_all_duplicates(self):
        """全重复 → 只剩一个。"""
        proxies = ["1.2.3.4:8080", "1.2.3.4:8080", "1.2.3.4:8080"]
        result = list(yield_unique_proxies(proxies))
        assert result == ["1.2.3.4:8080"]

    def test_empty_list(self):
        """空列表 → 空。"""
        result = list(yield_unique_proxies([]))
        assert result == []
