"""
维基百科行业公司列表爬虫
免费、稳定、无反爬，覆盖全行业的全球知名企业。

支持的行业分类（可扩展）：
- retail: 零售/超市
- electronics: 电子/科技
- fashion: 服装/时尚
- food: 食品饮料
- automotive: 汽车
- pharmaceutical: 医药
- energy: 能源
- construction: 建筑/建材
- furniture: 家居/家具
- cosmetics: 化妆品/个人护理
"""
import logging
import re
from typing import List, Dict
from .base import BaseDirectorySource, CompanyLead

logger = logging.getLogger(__name__)

# 维基百科各行业公司列表页面
INDUSTRY_PAGES: Dict[str, List[str]] = {
    'retail': [
        'List_of_largest_retail_companies',
        'List_of_supermarket_chains',
        'List_of_discount_superstores',
    ],
    'electronics': [
        'List_of_largest_technology_companies_by_revenue',
        'List_of_consumer_electronics_brands',
    ],
    'fashion': [
        'List_of_largest_apparel_companies',
        'List_of_clothing_brands',
    ],
    'food': [
        'List_of_largest_food_companies',
        'List_of_beverage_companies',
    ],
    'automotive': [
        'List_of_automobile_manufacturers',
        'List_of_largest_automotive_suppliers',
    ],
    'pharmaceutical': [
        'List_of_largest_pharmaceutical_companies',
    ],
    'energy': [
        'List_of_largest_oil_and_gas_companies',
        'List_of_renewable_energy_companies',
    ],
    'construction': [
        'List_of_largest_construction_companies',
        'List_of_building_material_companies',
    ],
    'furniture': [
        'List_of_furniture_companies',
        'List_of_home_improvement_retailers',
    ],
    'cosmetics': [
        'List_of_cosmetics_brands',
    ],
    'general': [
        'List_of_largest_companies_by_revenue',
        'List_of_largest_companies_in_the_United_States_by_revenue',
        'List_of_largest_companies_of_Europe',
    ],
}

# 发达国家优先排序（有钱国家）
PRIORITY_COUNTRIES = [
    'United States', 'Germany', 'Japan', 'United Kingdom', 'France',
    'Switzerland', 'Netherlands', 'South Korea', 'Canada', 'Australia',
    'Sweden', 'Italy', 'Spain', 'Belgium', 'Austria', 'Norway',
    'Denmark', 'Finland', 'Ireland', 'Singapore', 'UAE', 'Saudi Arabia',
    'Israel', 'New Zealand', 'Hong Kong', 'Taiwan',
]


class WikipediaDirectorySource(BaseDirectorySource):
    """维基百科行业公司列表爬虫"""

    name = 'wikipedia'
    base_url = 'https://en.wikipedia.org/wiki/'
    request_delay = 1.0  # 维基百科友好，延迟可以短一些

    def search(self, keyword: str = '', country: str = '') -> List[CompanyLead]:
        """
        从维基百科抓取行业公司列表。
        keyword: 行业关键词（retail/electronics/fashion 等），为空则抓 general
        country: 可选国家筛选
        """
        from bs4 import BeautifulSoup

        leads = []
        pages = self._get_pages_for_keyword(keyword)

        for page_title in pages:
            url = self.base_url + page_title
            logger.info(f"[wikipedia] 抓取: {page_title}")
            html = self._fetch(url)
            if not html:
                continue

            soup = BeautifulSoup(html, 'html.parser')
            table_leads = self._parse_wikitables(soup, page_title)
            list_leads = self._parse_wikilists(soup, page_title)
            leads.extend(table_leads)
            leads.extend(list_leads)

        # 去重（按公司名）
        seen = set()
        unique = []
        for lead in leads:
            key = lead.company_name.lower().strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(lead)

        # 国家筛选
        if country:
            unique = [l for l in unique if country.lower() in (l.country or '').lower()]

        # 发达国家优先排序
        unique.sort(key=lambda l: self._country_priority(l.country))

        logger.info(f"[wikipedia] 共获取 {len(unique)} 家公司")
        return unique

    def _get_pages_for_keyword(self, keyword: str) -> List[str]:
        """根据关键词确定要抓取的维基百科页面"""
        keyword = (keyword or '').lower().strip()
        if not keyword or keyword == 'all' or keyword == 'general':
            return INDUSTRY_PAGES['general'] + INDUSTRY_PAGES['retail']

        # 精确匹配行业
        for industry, pages in INDUSTRY_PAGES.items():
            if industry in keyword or keyword in industry:
                return pages

        # 模糊匹配
        for industry, pages in INDUSTRY_PAGES.items():
            if any(w in keyword for w in industry.split('_')):
                return pages

        # 默认抓 general + retail
        return INDUSTRY_PAGES['general']

    def _parse_wikitables(self, soup, page_title: str) -> List[CompanyLead]:
        """解析维基百科表格中的公司数据"""
        leads = []
        tables = soup.find_all('table', class_='wikitable')

        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue

            # 解析表头，确定列索引
            headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(['th', 'td'])]
            name_idx = self._find_column(headers, ['company', 'name', 'organisation', 'organization'])
            country_idx = self._find_column(headers, ['country', 'headquarters', 'location', 'origin'])
            revenue_idx = self._find_column(headers, ['revenue', 'sales'])

            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) <= max(name_idx, country_idx):
                    continue

                name_cell = cells[name_idx] if name_idx < len(cells) else None
                if not name_cell:
                    continue

                company_name = name_cell.get_text(strip=True)
                # 清理引用标记 [1][2]
                company_name = re.sub(r'\[\d+\]', '', company_name).strip()
                if not company_name or len(company_name) < 2:
                    continue

                # 提取官网链接（如果表格中有）
                website = ''
                link = name_cell.find('a', href=True)
                if link and link['href'].startswith('/wiki/'):
                    website = 'https://en.wikipedia.org' + link['href']

                country = ''
                if country_idx < len(cells):
                    country = cells[country_idx].get_text(strip=True)
                    country = re.sub(r'\[\d+\]', '', country).strip()

                leads.append(CompanyLead(
                    company_name=company_name,
                    website=website,
                    country=country,
                    industry=self._infer_industry(page_title),
                    source='wikipedia',
                    source_url=self.base_url + page_title,
                ))

        return leads

    def _parse_wikilists(self, soup, page_title: str) -> List[CompanyLead]:
        """解析维基百科列表式页面（非表格）"""
        leads = []
        # 找主要内容区域的列表
        content = soup.find('div', class_='mw-parser-output')
        if not content:
            return leads

        for li in content.find_all('li'):
            # 只取直接子元素的 li，避免嵌套
            if li.find_parent('li'):
                continue

            link = li.find('a', href=True)
            if not link:
                continue

            title = link.get('title', '')
            href = link['href']
            if not href.startswith('/wiki/') or ':' in href:
                continue

            company_name = link.get_text(strip=True)
            company_name = re.sub(r'\[\d+\]', '', company_name).strip()
            if not company_name or len(company_name) < 2:
                continue

            # 跳过明显不是公司的条目
            skip_words = ['list', 'category', 'template', 'file', 'portal', 'wikipedia', 'edit']
            if any(w in company_name.lower() for w in skip_words):
                continue

            leads.append(CompanyLead(
                company_name=company_name,
                website='https://en.wikipedia.org' + href,
                country='',
                industry=self._infer_industry(page_title),
                source='wikipedia',
                source_url=self.base_url + page_title,
            ))

        return leads

    @staticmethod
    def _find_column(headers, keywords):
        """找到包含关键词的列索引"""
        for i, h in enumerate(headers):
            if any(kw in h for kw in keywords):
                return i
        return 0

    @staticmethod
    def _infer_industry(page_title: str) -> str:
        """从页面标题推断行业"""
        page_lower = page_title.lower()
        industry_map = {
            'retail': '零售', 'supermarket': '零售', 'store': '零售',
            'technology': '科技', 'electronic': '电子', 'software': '科技',
            'apparel': '服装', 'clothing': '服装', 'fashion': '服装',
            'food': '食品', 'beverage': '食品',
            'automobile': '汽车', 'automotive': '汽车', 'car': '汽车',
            'pharmaceutical': '医药', 'drug': '医药',
            'oil': '能源', 'gas': '能源', 'energy': '能源',
            'construction': '建筑', 'building': '建筑',
            'furniture': '家居', 'home': '家居',
            'cosmetic': '化妆品', 'beauty': '化妆品',
        }
        for key, value in industry_map.items():
            if key in page_lower:
                return value
        return '综合'

    @staticmethod
    def _country_priority(country: str) -> int:
        """国家优先级排序（发达国家优先）"""
        if not country:
            return 999
        for i, pc in enumerate(PRIORITY_COUNTRIES):
            if pc.lower() in country.lower():
                return i
        return 100
