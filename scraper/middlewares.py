"""
自定义下载中间件：
1. RandomUserAgentMiddleware —— 随机 User-Agent 轮换
2. ProxyMiddleware —— 代理池支持（可选）
"""
import random
import requests
from scrapy import signals


class RandomUserAgentMiddleware:
    """随机轮换 User-Agent，降低被识别为爬虫的概率。"""

    def __init__(self, user_agents):
        self.user_agents = user_agents

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.getlist('USER_AGENT_LIST'))

    def process_request(self, request, spider):
        ua = random.choice(self.user_agents)
        request.headers['User-Agent'] = ua


class ProxyMiddleware:
    """
    代理池中间件。
    通过 PROXY_API_URL 环境变量配置代理获取接口。
    若未配置，则不使用代理（直连）。
    """

    def __init__(self, proxy_api_url, enabled):
        self.proxy_api_url = proxy_api_url
        self.enabled = enabled
        self._proxy_cache = []
        self._proxy_index = 0

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            proxy_api_url=crawler.settings.get('PROXY_API_URL', ''),
            enabled=crawler.settings.get('PROXY_ENABLED', False),
        )

    def _fetch_proxy(self):
        """从代理 API 获取新代理。"""
        try:
            resp = requests.get(self.proxy_api_url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # 兼容多种代理 API 返回格式
                if isinstance(data, list):
                    self._proxy_cache = [f"http://{p}" for p in data]
                elif isinstance(data, dict) and 'proxy' in data:
                    self._proxy_cache = [data['proxy']]
                elif isinstance(data, dict) and 'data' in data:
                    self._proxy_cache = [f"http://{p}" for p in data['data']]
        except Exception:
            pass

    def process_request(self, request, spider):
        if not self.enabled:
            return

        # 缓存耗尽时重新获取
        if self._proxy_index >= len(self._proxy_cache):
            self._fetch_proxy()
            self._proxy_index = 0

        if self._proxy_cache:
            proxy = self._proxy_cache[self._proxy_index]
            request.meta['proxy'] = proxy
            self._proxy_index += 1
