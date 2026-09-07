"""
EuroPages 欧洲企业目录爬虫
覆盖欧洲数百万家企业，按行业和国家筛选。
注意：EuroPages 有反爬机制，需要设置合理延迟。
"""
import logging
import re
from typing import List
from urllib.parse import quote_plus
from .base import BaseDirectorySource, CompanyLead

logger = logging.getLogger(__name__)


class EuroPagesDirectorySource(BaseDirectorySource):
    """EuroPages 欧洲企业目录爬虫"""

    name = 'europages'
    base_url = 'https://www.europages.co.uk'
    request_delay = 3.0  # EuroPages 反爬较严，延迟长一些

    def search(self, keyword: str = '', country: str = '') -> List[CompanyLead]:
        """
        在 EuroPages 搜索企业。
        keyword: 行业关键词（如 electronics, furniture, cosmetics）
        country: 可选国家代码（如 uk, de, fr）
        """
        from bs4 import BeautifulSoup

        if not keyword:
            keyword = 'retail'

        leads = []
        for page in range(1, self.max_pages + 1):
            url = self._build_search_url(keyword, country, page)
            logger.info(f"[europages] 抓取第 {page} 页: {keyword}")
            html = self._fetch(url)
            if not html:
                break

            soup = BeautifulSoup(html, 'html.parser')
            page_leads = self._parse_results(soup, keyword)
            if not page_leads:
                break
            leads.extend(page_leads)

            # 检查是否有下一页
            if not self._has_next_page(soup):
                break

        logger.info(f"[europages] 共获取 {len(leads)} 家公司")
        return leads

    def _build_search_url(self, keyword: str, country: str, page: int) -> str:
        """构建搜索 URL"""
        kw = quote_plus(keyword)
        if country:
            url = f"{self.base_url}/companies/{country}/{kw}/pg-{page}.html"
        else:
            url = f"{self.base_url}/companies/{kw}/pg-{page}.html"
        return url

    def _parse_results(self, soup, keyword: str) -> List[CompanyLead]:
        """解析搜索结果页"""
        leads = []

        # EuroPages 结果卡片
        cards = soup.find_all('div', class_=re.compile(r'company-card|result-item|ep-ecard'))
        if not cards:
            # 尝试其他选择器
            cards = soup.find_all('article', class_=re.compile(r'company|result'))
        if not cards:
            cards = soup.find_all('div', {'data-testid': re.compile(r'company|card')})

        for card in cards:
            try:
                lead = self._parse_card(card, keyword)
                if lead:
                    leads.append(lead)
            except Exception as e:
                logger.debug(f"[europages] 解析卡片失败: {e}")
                continue

        return leads

    def _parse_card(self, card, keyword: str) -> CompanyLead | None:
        """解析单个公司卡片"""
        # 公司名
        name_el = card.find(['h2', 'h3', 'a'], class_=re.compile(r'title|name|company'))
        if not name_el:
            name_el = card.find(['h2', 'h3'])
        if not name_el:
            return None

        company_name = name_el.get_text(strip=True)
        company_name = re.sub(r'\s+', ' ', company_name).strip()
        if not company_name or len(company_name) < 2:
            return None

        # 官网链接
        website = ''
        link = name_el.find('a', href=True) if name_el.name != 'a' else name_el
        if link and link.get('href'):
            href = link['href']
            if href.startswith('http') and 'europages' not in href:
                website = href

        # 地址/国家
        country = ''
        city = ''
        addr_el = card.find(['span', 'p', 'div'], class_=re.compile(r'address|location|country'))
        if addr_el:
            addr_text = addr_el.get_text(strip=True)
            parts = [p.strip() for p in addr_text.split(',') if p.strip()]
            if len(parts) >= 2:
                city = parts[-2]
                country = parts[-1]
            elif parts:
                country = parts[-1]

        return CompanyLead(
            company_name=company_name,
            website=website,
            country=country,
            city=city,
            industry=keyword,
            source='europages',
            source_url=self.base_url,
        )

    def _has_next_page(self, soup) -> bool:
        """检查是否有下一页"""
        next_btn = soup.find(['a', 'button'], string=re.compile(r'Next|Suivant|Weiter', re.I))
        return next_btn is not None
