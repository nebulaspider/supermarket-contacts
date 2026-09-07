"""
Made-in-China 目录数据源
从 Made-in-China.com 搜索中国供应商信息。
Made-in-China 是全球知名的中国 B2B 平台。
"""
import logging
from typing import List
from urllib.parse import quote_plus

from .base import CompanyLead, BaseDirectorySource

logger = logging.getLogger(__name__)


class MadeInChinaDirectorySource(BaseDirectorySource):
    """Made-in-China 企业目录搜索"""

    name = "Made-in-China"
    base_url = "https://www.made-in-china.com"

    def search(self, keyword: str, country: str = "", max_results: int = 20) -> List[CompanyLead]:
        """
        搜索 Made-in-China 上的供应商。
        """
        leads = []
        try:
            import requests
            from bs4 import BeautifulSoup

            search_url = f"{self.base_url}/productdirectory.do?subaction=hunt&style=b&code=0&word={quote_plus(keyword)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'en-US,en;q=0.9',
            }

            resp = requests.get(search_url, headers=headers, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"Made-in-China 搜索失败 {keyword}: HTTP {resp.status_code}")
                return leads

            soup = BeautifulSoup(resp.text, 'html.parser')

            # 搜索结果中的公司/产品卡片
            cards = soup.select('.product-list-item, .company-item, [data-company], .serach-item')
            for card in cards[:max_results]:
                try:
                    # 公司名
                    name_el = card.select_one('.company-name a, .seller-name, [data-company-name]')
                    if not name_el:
                        # 尝试从产品卡片中提取供应商
                        name_el = card.select_one('a[title*="Manufacturer"], a[title*="Supplier"]')
                    if not name_el:
                        continue
                    company_name = name_el.get_text(strip=True) or name_el.get('title', '')
                    if not company_name or len(company_name) < 2:
                        continue

                    # 网站
                    website = ''
                    if name_el.get('href'):
                        href = name_el['href']
                        if href.startswith('http') and 'made-in-china.com' not in href:
                            website = href

                    # 位置
                    location = 'China'
                    loc_el = card.select_one('.company-location, [data-province], .province')
                    if loc_el:
                        location = loc_el.get_text(strip=True) + ', China'

                    # 产品
                    product = keyword
                    prod_el = card.select_one('.product-name, h3 a')
                    if prod_el:
                        product = prod_el.get_text(strip=True)

                    leads.append(CompanyLead(
                        company_name=company_name,
                        country='China',
                        city=location,
                        website=website,
                        industry=keyword,
                        product_categories=product,
                        source='Made-in-China',
                        source_url=search_url,
                    ))
                except Exception as e:
                    logger.debug(f"解析 Made-in-China 卡片失败: {e}")
                    continue

            logger.info(f"Made-in-China 搜索 '{keyword}': 找到 {len(leads)} 家公司")

        except ImportError:
            logger.warning("requests/bs4 未安装，跳过 Made-in-China")
        except Exception as e:
            logger.warning(f"Made-in-China 搜索异常 {keyword}: {e}")

        return leads
