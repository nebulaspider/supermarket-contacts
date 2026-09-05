"""
自动发现模块：从公开渠道（维基百科、商业目录）自动发现新的超市品牌。

策略：
1. 从维基百科 "List of supermarket chains" 页面提取品牌列表
2. 从已知品牌的官网 footer / about 页面发现关联品牌
3. 生成待抓取的新品牌候选列表
4. 与现有数据去重，输出新发现的品牌

注意：本模块只做"发现"，不做深度抓取。
发现的品牌会交给对应的品牌爬虫或通用爬虫去抓取详细信息。
"""
import re
import json
import os
import logging
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s [auto_discover] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

# 维基百科超市连锁列表页面
WIKI_SOURCES = [
    'https://en.wikipedia.org/wiki/List_of_supermarket_chains',
    'https://en.wikipedia.org/wiki/List_of_hypermarkets',
]

# 已知品牌关键词（用于过滤非超市条目）
SUPERMARKET_KEYWORDS = [
    'supermarket', 'hypermarket', 'grocery', 'food retail',
    'convenience store', 'discount store', 'cash and carry',
    '超市', '大卖场', '便利店', '百货',
]


def fetch_page(url, timeout=15):
    """安全获取页面内容。"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.warning(f"获取页面失败 {url}: {e}")
        return None


def extract_from_wikipedia(html):
    """
    从维基百科列表页面提取超市品牌名称和国家。
    返回: [{'name': ..., 'country': ..., 'source': 'wikipedia'}, ...]
    """
    if not html:
        return []

    soup = BeautifulSoup(html, 'lxml')
    results = []

    # 维基百科的列表通常在 <ul> 或 <table> 中
    # 策略1: 从表格中提取
    for table in soup.find_all('table', class_='wikitable'):
        for row in table.find_all('tr')[1:]:  # 跳过表头
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                name = cells[0].get_text(strip=True)
                country = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                if name and len(name) < 100:
                    results.append({
                        'name': re.sub(r'\[.*?\]', '', name).strip(),
                        'country': re.sub(r'\[.*?\]', '', country).strip(),
                        'source': 'wikipedia',
                    })

    # 策略2: 从列表项中提取
    for li in soup.select('.mw-parser-output > ul li'):
        text = li.get_text(strip=True)
        if text and len(text) < 80 and not text.startswith('See'):
            # 尝试提取 "品牌 (国家)" 格式
            match = re.match(r'^(.+?)\s*[（(](.+?)[）)]', text)
            if match:
                results.append({
                    'name': match.group(1).strip(),
                    'country': match.group(2).strip(),
                    'source': 'wikipedia',
                })
            elif len(text) < 50:
                results.append({
                    'name': text,
                    'country': '',
                    'source': 'wikipedia',
                })

    return results


def load_existing_brands(data_path):
    """加载已有数据中的品牌名称集合，用于去重。"""
    if not os.path.exists(data_path):
        return set()
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {item.get('company_name', '').lower() for item in data}


def discover_new_brands(data_path='../data/clients.json', output_path='../data/new_brands.json'):
    """
    主入口：自动发现新品牌。
    1. 从维基百科等来源提取品牌列表
    2. 与现有数据去重
    3. 输出新发现的品牌列表
    """
    data_path = os.path.join(os.path.dirname(__file__), data_path)
    output_path = os.path.join(os.path.dirname(__file__), output_path)

    existing = load_existing_brands(data_path)
    logger.info(f"已有品牌数: {len(existing)}")

    all_candidates = []

    # 从维基百科发现
    for url in WIKI_SOURCES:
        logger.info(f"正在扫描: {url}")
        html = fetch_page(url)
        candidates = extract_from_wikipedia(html)
        all_candidates.extend(candidates)
        logger.info(f"  发现 {len(candidates)} 个候选")

    # 去重（名称层面）
    seen_names = set()
    unique_candidates = []
    for c in all_candidates:
        name_lower = c['name'].lower()
        if name_lower not in seen_names and name_lower not in existing:
            seen_names.add(name_lower)
            unique_candidates.append(c)

    # 添加发现时间
    now = datetime.now(timezone.utc).isoformat()
    for c in unique_candidates:
        c['discovered_at'] = now
        c['status'] = 'pending'  # pending / scraping / done / failed

    # 输出
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(unique_candidates, f, ensure_ascii=False, indent=2)

    logger.info(f"新发现品牌: {len(unique_candidates)} 个，已保存到 {output_path}")
    return unique_candidates


if __name__ == '__main__':
    discover_new_brands()
