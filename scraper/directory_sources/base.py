"""
目录爬虫基类
所有商业目录数据源都继承这个基类，实现统一的接口。
"""
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CompanyLead:
    """从目录中提取的公司线索（还未提取联系方式）"""
    company_name: str
    website: str = ''
    country: str = ''
    city: str = ''
    industry: str = ''
    source: str = ''          # 数据来源目录
    source_url: str = ''      # 来源页面 URL
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'company_name': self.company_name,
            'website': self.website,
            'country': self.country,
            'city': self.city,
            'industry': self.industry,
            'source_url': self.source_url,
        }


class BaseDirectorySource(ABC):
    """目录数据源基类"""

    # 子类必须设置
    name: str = 'base'
    base_url: str = ''
    request_delay: float = 2.0  # 请求延迟（秒），避免被封

    def __init__(self, max_pages: int = 5, timeout: int = 15):
        self.max_pages = max_pages
        self.timeout = timeout
        self.session = None  # 延迟初始化 requests.Session

    def _get_session(self):
        """获取 requests session（延迟导入，方便本地无依赖时导入模块）"""
        if self.session is None:
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': (
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Safari/537.36'
                ),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8',
            })
        return self.session

    def _fetch(self, url: str) -> Optional[str]:
        """安全地获取页面 HTML"""
        try:
            session = self._get_session()
            resp = session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            time.sleep(self.request_delay)
            return resp.text
        except Exception as e:
            logger.warning(f"[{self.name}] 抓取失败 {url}: {e}")
            return None

    @abstractmethod
    def search(self, keyword: str, country: str = '') -> List[CompanyLead]:
        """
        根据行业关键词搜索公司列表。
        子类必须实现这个方法。
        """
        pass

    def __repr__(self):
        return f"<DirectorySource:{self.name}>"
