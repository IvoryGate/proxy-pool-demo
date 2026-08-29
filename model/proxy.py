"""Proxy 数据模型：池子里每个代理的"身份证"。

对应 Redis hash 里的一个 value（JSON 字符串）。
"""

import json
from typing import Optional


class Proxy:
    proxy: str
    https: bool
    fail_count: int
    check_count: int
    last_status: bool
    last_time: Optional[str]

    def __init__(
        self,
        proxy: str,
        https: bool = False,
        fail_count: int = 0,
        check_count: int = 0,
        last_status: bool = False,
        last_time: Optional[str] = None,
    ):
        self.proxy = proxy
        self.https = https
        self.fail_count = fail_count
        self.check_count = check_count
        self.last_status = last_status
        self.last_time = last_time

    def to_json(self) -> str:
        """序列化成 JSON 字符串，存进 Redis。"""
        return json.dumps(self.__dict__, ensure_ascii=False)

    @classmethod
    def create_from_json(cls, json_str: str) -> "Proxy":
        """从 JSON 还原对象；缺字段用默认值兜底（向后兼容）。"""
        data: dict = json.loads(json_str)
        defaults: dict = {
            "proxy": "",
            "https": False,
            "fail_count": 0,
            "check_count": 0,
            "last_status": False,
            "last_time": None,
        }
        defaults.update(data)
        return cls(**defaults)
