"""Proxy 数据模型：池子里每个代理的“身份证”。

对应 Redis hash 里的一个 value（JSON 字符串）。
"""

import json


class Proxy:
    def __init__(self, proxy, https=False, fail_count=0, check_count=0,
                 last_status=False, last_time=None):
        self.proxy = proxy              # ip:port，唯一标识
        self.https = https              # 是否支持 https
        self.fail_count = fail_count    # 连续失败次数（淘汰依据）
        self.check_count = check_count  # 累计校验次数
        self.last_status = last_status  # 上次校验是否成功
        self.last_time = last_time      # 上次校验时间

    def to_json(self):
        """序列化成 JSON 字符串，存进 Redis。"""
        return json.dumps(self.__dict__, ensure_ascii=False)

    @classmethod
    def create_from_json(cls, json_str):
        """从 JSON 还原对象；缺字段用默认值兜底（向后兼容）。"""
        data = json.loads(json_str)
        defaults = {"proxy": "", "https": False, "fail_count": 0,
                    "check_count": 0, "last_status": False, "last_time": None}
        defaults.update(data)
        return cls(**defaults)
