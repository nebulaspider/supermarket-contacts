"""
IndiaMART 目录数据源
从 IndiaMART 搜索供应商/买家信息。
IndiaMART 是印度最大的 B2B 平台，有大量供应商和买家信息。
"""
import logging
import re
from typing import List, Optional
from urllib.parse import quote_plus

from .base import CompanyLead, BaseDirectorySource

logger = logging.getLogger(__name__)


class IndiaMARTDirectorySource(BaseDirectorySource):
    """IndiaMART 企业目录搜索"""

    name = "IndiaMART"
    base_url = "https://dir.indiamart.com"

    def search(self, keyword: str, country: str = "", max_results: int = 20) -> List[CompanyLead]:
        """
        搜索 IndiaMART 上的供应商。
        注意：IndiaMART 有反爬机制，可能需要代理。
        """
        leads = []
        try:
            import requests
            from bs4 import BeautifulSoup

            search_url = f"{self.base_url}/search.mp?ss={quote_plus(keyword)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'en-US,en;q=0.9',
            }

            resp = requests.get(search_url, headers=headers, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"IndiaMART 搜索失败 {keyword}: HTTP {resp.status_code}")
                return leads

            soup = BeautifulSoup(resp.text, 'html.parser')

            # IndiaMART 搜索结果中的公司卡片
            cards = soup.select('.cntanr, .company-list, [data-name]')
            for card in cards[:max_results]:
                try:
                    # 公司名
                    name_el = card.select_one('.company-name, h2 a, [data-company-name]')
                    if not name_el:
                        continue
                    company_name = name_el.get_text(strip=True)
                    if not company_name or len(company_name) < 2:
                        continue

                    # 网站链接
                    website = ''
                    link_el = card.select_one('a[href*="http"]')
                    if link_el and link_el.get('href'):
                        href = link_el['href']
                        if 'indiamart.com' not in href:
                            website = href

                    # 位置信息
                    location = ''
                    loc_el = card.select_one('.company-location, [data-city], .loc')
                    if loc_el:
                        location = loc_el.get_text(strip=True)

                    # 产品/行业
                    product = keyword
                    prod_el = card.select_one('.product-name, [data-product]')
                    if prod_el:
                        product = prod_el.get_text(strip=True)

                    leads.append(CompanyLead(
                        company_name=company_name,
                        country=location or 'India',
                        city=location,
                        website=website,
                        industry=keyword,
                        product_categories=product,
                        source='IndiaMART',
                        source_url=search_url,
                    ))
                except Exception as e:
                    logger.debug(f"解析 IndiaMART 卡片失败: {e}")
                    continue

            logger.info(f"IndiaMART 搜索 '{keyword}': 找到 {len(leads)} 家公司")

        except ImportError:
            logger.warning("requests/bs4 未安装，跳过 IndiaMART")
        except Exception as e:
            logger.warning(f"IndiaMART 搜索异常 {keyword}: {e}")

        return leads
