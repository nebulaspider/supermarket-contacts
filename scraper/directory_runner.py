"""
目录爬虫主入口
流程：目录搜索（维基百科/EuroPages）→ 官网联系方式提取 → 输出 JSON
纯免费方案，支持全行业、多国家。
"""
import json
import logging
import os
import sys
from datetime import datetime
from typing import List, Dict

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.directory_sources.wikipedia import WikipediaDirectorySource
from scraper.directory_sources.europages import EuroPagesDirectorySource
from scraper.directory_sources.indiamart import IndiaMARTDirectorySource
from scraper.directory_sources.made_in_china import MadeInChinaDirectorySource
from scraper.contact_extractor import ContactExtractor
from scraper.directory_sources.base import CompanyLead


def extract_website_from_wikipedia(wikipedia_url: str) -> str:
    """从维基百科公司页面的信息框中提取官方网站链接"""
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        resp = requests.get(wikipedia_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return ''

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 方法1：从 infobox 中找 "Website" 行
        infobox = soup.find('table', class_='infobox')
        if infobox:
            for row in infobox.find_all('tr'):
                header = row.find('th')
                if header and 'website' in header.get_text().lower():
                    link = row.find('a', class_='external')
                    if link and link.get('href'):
                        return link['href'].split('?')[0].rstrip('/')

        # 方法2：找页面中第一个外部链接（通常是官网）
        for link in soup.find_all('a', class_='external'):
            href = link.get('href', '')
            if href and 'wikipedia.org' not in href and 'wikimedia' not in href:
                return href.split('?')[0].rstrip('/')

        return ''
    except Exception as e:
        logger.warning(f"从维基百科提取官网失败 {wikipedia_url}: {e}")
        return ''

logger = logging.getLogger(__name__)

# 支持的行业列表（全行业）
SUPPORTED_INDUSTRIES = [
    'retail', 'electronics', 'fashion', 'food', 'automotive',
    'pharmaceutical', 'energy', 'construction', 'furniture',
    'cosmetics', 'general',
]

# 行业中文名映射
INDUSTRY_NAMES = {
    'retail': '零售/超市',
    'electronics': '电子/科技',
    'fashion': '服装/时尚',
    'food': '食品饮料',
    'automotive': '汽车',
    'pharmaceutical': '医药',
    'energy': '能源',
    'construction': '建筑/建材',
    'furniture': '家居/家具',
    'cosmetics': '化妆品',
    'general': '综合（全球500强）',
}


def run_directory_crawl(
    industries: List[str] = None,
    country: str = '',
    max_companies: int = 100,
    extract_contacts: bool = True,
    output_path: str = 'data/clients_directory.json',
) -> List[Dict]:
    """
    运行目录爬虫。

    Args:
        industries: 行业列表，如 ['retail', 'electronics']，为空则抓 general
        country: 国家筛选，如 'us', 'de'，为空则全球
        max_companies: 最大抓取公司数
        extract_contacts: 是否访问官网提取联系方式（较慢但数据更全）
        output_path: 输出文件路径

    Returns:
        客户数据列表
    """
    if industries is None:
        industries = ['general', 'retail']

    all_leads = []

    # ===== 第1步：从目录源获取公司列表 =====
    sources = [
        WikipediaDirectorySource(max_pages=3),
        EuroPagesDirectorySource(max_pages=2),
        IndiaMARTDirectorySource(),
        MadeInChinaDirectorySource(),
    ]

    for industry in industries:
        logger.info(f"=== 开始抓取行业: {INDUSTRY_NAMES.get(industry, industry)} ===")
        for source in sources:
            try:
                leads = source.search(keyword=industry, country=country)
                logger.info(f"  [{source.name}] 获取 {len(leads)} 家公司")
                all_leads.extend(leads)
            except Exception as e:
                logger.error(f"  [{source.name}] 抓取失败: {e}")
                continue

    # 去重
    seen = set()
    unique_leads = []
    for lead in all_leads:
        key = lead.company_name.lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique_leads.append(lead)

    logger.info(f"去重后共 {len(unique_leads)} 家公司")

    # 限制数量
    unique_leads = unique_leads[:max_companies]

    # ===== 第2步：访问官网提取联系方式 =====
    results = []
    if extract_contacts:
        extractor = ContactExtractor(timeout=10, request_delay=1.0)
        for i, lead in enumerate(unique_leads):
            logger.info(f"[{i+1}/{len(unique_leads)}] 提取联系方式: {lead.company_name}")

            record = lead.to_dict()
            record['industry'] = INDUSTRY_NAMES.get(lead.industry, lead.industry)
            record['scraped_at'] = datetime.utcnow().isoformat() + 'Z'
            record['data_quality'] = 0

            # 如果 website 是维基百科链接，先从维基页面提取真实官网
            if lead.website and 'wikipedia.org' in lead.website:
                real_website = extract_website_from_wikipedia(lead.website)
                if real_website:
                    record['website'] = real_website
                    lead.website = real_website
                else:
                    record['website'] = ''

            # 提取联系方式
            if lead.website and 'wikipedia.org' not in lead.website:
                contacts = extractor.extract(lead.website)
                record.update(contacts)
            elif not record.get('website'):
                record['website'] = ''

            results.append(record)
    else:
        for lead in unique_leads:
            record = lead.to_dict()
            record['industry'] = INDUSTRY_NAMES.get(lead.industry, lead.industry)
            record['scraped_at'] = datetime.utcnow().isoformat() + 'Z'
            record['data_quality'] = 0
            results.append(record)

    # ===== 第3步：保存 =====
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    logger.info(f"已保存 {len(results)} 条数据到 {output_path}")
    return results


def merge_with_existing(directory_data: List[Dict], existing_path: str = 'data/clients.json') -> List[Dict]:
    """将目录爬虫数据与现有数据合并"""
    if not os.path.exists(existing_path):
        return directory_data

    with open(existing_path, 'r', encoding='utf-8') as f:
        existing = json.load(f)

    # 按公司名去重合并
    seen = {item['company_name'].lower().strip() for item in existing}
    merged = list(existing)

    for item in directory_data:
        key = item['company_name'].lower().strip()
        if key not in seen:
            merged.append(item)
            seen.add(key)

    return merged


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    )

    # 默认抓取：综合 + 零售 + 电子 + 家居
    industries = sys.argv[1:] if len(sys.argv) > 1 else ['general', 'retail', 'electronics', 'furniture']
    country = sys.argv[2] if len(sys.argv) > 2 else ''

    print(f"行业: {industries}")
    print(f"国家: {country or '全球'}")
    print("=" * 50)

    data = run_directory_crawl(
        industries=industries,
        country=country,
        max_companies=50,
        extract_contacts=True,
    )

    print(f"\n完成！共 {len(data)} 条客户数据")
    print(f"有邮箱: {sum(1 for d in data if d.get('email'))}")
    print(f"有电话: {sum(1 for d in data if d.get('phone'))}")
