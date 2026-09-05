"""
数据管理器：合并、去重、验证、质量评分、导出。

全自动化管线的核心组件：
1. 合并爬虫输出 + 手动补充数据 + 自动发现的新品牌
2. 智能去重（公司名+国家，模糊匹配）
3. 数据验证（邮箱格式、电话号码、URL有效性）
4. 质量评分
5. 生成数据质量报告
6. 输出最终 clients.json
"""
import re
import json
import os
import logging
from datetime import datetime, timezone
from difflib import SequenceMatcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s [data_manager] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# 字段权重（用于质量评分）
FIELD_WEIGHTS = {
    # 基本信息
    'company_name': 10, 'country': 8, 'city': 4, 'address': 4, 'website': 6,
    # 行业属性
    'industry': 6, 'company_size': 3, 'founded_year': 2, 'parent_company': 2,
    'store_count': 3, 'product_categories': 4,
    # 关键联系人（高价值）
    'contact_person': 8, 'position': 6, 'department': 4,
    'contact_email': 8, 'contact_phone': 5, 'contact_linkedin': 4,
    # 公司联系方式
    'email': 8, 'phone': 8,
    'whatsapp': 3, 'wechat': 3, 'linkedin': 6,
    'facebook': 1, 'twitter': 1, 'instagram': 1, 'youtube': 1,
}

# 邮箱正则
EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
# 电话正则（至少7位数字）
PHONE_RE = re.compile(r'^\+?[\d\s\-()]{7,}$')
# URL 正则
URL_RE = re.compile(r'^https?://[^\s/$.?#].[^\s]*$', re.I)


def clean_value(value):
    """清洗单个字段值。"""
    if not value:
        return ''
    if isinstance(value, str):
        value = value.strip()
        # 去除不可见字符
        value = re.sub(r'[\u200b-\u200f\ufeff]', '', value)
    return value


def validate_email(email):
    """验证邮箱格式。"""
    if not email:
        return False
    # 过滤常见无效域名
    invalid_domains = {'example.com', 'domain.com', 'test.com', 'email.com', 'yourdomain.com'}
    if email.split('@')[-1].lower() in invalid_domains:
        return False
    return bool(EMAIL_RE.match(email))


def validate_phone(phone):
    """验证电话号码格式。"""
    if not phone:
        return False
    digits = re.sub(r'[^\d]', '', phone)
    return 7 <= len(digits) <= 15


def validate_url(url):
    """验证URL格式。"""
    if not url:
        return False
    return bool(URL_RE.match(url))


def normalize_company_name(name):
    """标准化公司名称用于去重比较。"""
    if not name:
        return ''
    name = name.lower().strip()
    # 去除常见后缀
    suffixes = [' inc', ' ltd', ' llc', ' corp', ' corporation', ' group',
                ' co', ' company', ' holdings', ' supermarkets', ' supermarket',
                ' gmbh', ' ag', ' sa', ' s.a.', ' b.v.', ' pte', ' pte ltd']
    for s in suffixes:
        name = re.sub(re.escape(s) + r'$', '', name)
    return name.strip()


def is_duplicate(item1, item2, threshold=0.85):
    """判断两条数据是否重复（公司名+国家模糊匹配）。"""
    name1 = normalize_company_name(item1.get('company_name', ''))
    name2 = normalize_company_name(item2.get('company_name', ''))
    if not name1 or not name2:
        return False

    # 精确匹配
    if name1 == name2:
        # 国家也匹配（或一方为空）
        c1 = (item1.get('country') or '').lower()
        c2 = (item2.get('country') or '').lower()
        if not c1 or not c2 or c1 == c2:
            return True

    # 模糊匹配
    similarity = SequenceMatcher(None, name1, name2).ratio()
    if similarity >= threshold:
        c1 = (item1.get('country') or '').lower()
        c2 = (item2.get('country') or '').lower()
        if not c1 or not c2 or c1 == c2:
            return True

    return False


def merge_items(existing, new):
    """合并两条数据，保留更完整的字段。"""
    merged = dict(existing)
    for key, value in new.items():
        if not value:
            continue
        existing_val = merged.get(key)
        # 新值非空且旧值为空 → 用新值
        if not existing_val:
            merged[key] = value
        # 新值更长（通常更完整）→ 用新值
        elif isinstance(value, str) and isinstance(existing_val, str):
            if len(value) > len(existing_val) and key not in ('company_name', 'country'):
                merged[key] = value
    return merged


def calculate_quality(item):
    """计算数据质量评分。"""
    score = 0
    for field, weight in FIELD_WEIGHTS.items():
        if item.get(field):
            # 验证通过的字段得满分，格式可疑的减半
            if field == 'email' and not validate_email(item[field]):
                score += weight // 2
            elif field == 'phone' and not validate_phone(item[field]):
                score += weight // 2
            elif field in ('website', 'linkedin', 'facebook', 'twitter', 'instagram', 'youtube'):
                if validate_url(item[field]):
                    score += weight
                else:
                    score += weight // 2
            else:
                score += weight
    return min(score, 100)


def load_json(path):
    """安全加载 JSON。"""
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"加载 {path} 失败: {e}")
        return []


def run_pipeline(scraper_output='../data/clients.scraped.json',
                 manual_data='../data/clients.manual.json',
                 output='../data/clients.json',
                 report_path='../data/quality_report.json'):
    """
    运行完整数据管理管线。

    流程：
    1. 加载爬虫输出 + 手动补充数据
    2. 清洗所有字段
    3. 智能去重合并
    4. 验证数据有效性
    5. 计算质量评分
    6. 生成质量报告
    7. 输出最终数据
    """
    base_dir = os.path.dirname(__file__)
    scraper_output = os.path.join(base_dir, scraper_output)
    manual_data = os.path.join(base_dir, manual_data)
    output = os.path.join(base_dir, output)
    report_path = os.path.join(base_dir, report_path)

    # 1. 加载数据
    scraped = load_json(scraper_output)
    manual = load_json(manual_data)
    # 如果没有爬虫输出，使用现有 clients.json 作为基础
    if not scraped:
        scraped = load_json(output)
    all_items = scraped + manual
    logger.info(f"加载数据: 爬虫 {len(scraped)} 条, 手动 {len(manual)} 条, 合计 {len(all_items)} 条")

    # 2. 清洗
    for item in all_items:
        for key in list(item.keys()):
            item[key] = clean_value(item.get(key))

    # 3. 智能去重合并
    deduped = []
    for item in all_items:
        found = False
        for i, existing in enumerate(deduped):
            if is_duplicate(existing, item):
                deduped[i] = merge_items(existing, item)
                found = True
                break
        if not found:
            deduped.append(item)
    logger.info(f"去重后: {len(deduped)} 条 (合并了 {len(all_items) - len(deduped)} 条重复)")

    # 4. 验证 + 5. 质量评分
    now = datetime.now(timezone.utc).isoformat()
    validation_stats = {'email_valid': 0, 'email_invalid': 0, 'phone_valid': 0, 'phone_invalid': 0}
    for item in deduped:
        # 邮箱验证
        if item.get('email'):
            if validate_email(item['email']):
                validation_stats['email_valid'] += 1
            else:
                validation_stats['email_invalid'] += 1
                item['email'] = item['email'].lower()  # 至少标准化
        # 电话验证
        if item.get('phone'):
            if validate_phone(item['phone']):
                validation_stats['phone_valid'] += 1
            else:
                validation_stats['phone_invalid'] += 1
        # 质量评分
        item['data_quality'] = calculate_quality(item)
        item['scraped_at'] = item.get('scraped_at') or now

    # 按质量排序
    deduped.sort(key=lambda x: x.get('data_quality', 0), reverse=True)

    # 6. 生成质量报告
    total = len(deduped)
    field_coverage = {}
    for field in FIELD_WEIGHTS:
        field_coverage[field] = sum(1 for item in deduped if item.get(field))

    quality_distribution = {
        'high (>=80)': sum(1 for i in deduped if i.get('data_quality', 0) >= 80),
        'medium (60-79)': sum(1 for i in deduped if 60 <= i.get('data_quality', 0) < 80),
        'low (<60)': sum(1 for i in deduped if i.get('data_quality', 0) < 60),
    }
    avg_quality = round(sum(i.get('data_quality', 0) for i in deduped) / total, 1) if total else 0

    report = {
        'generated_at': now,
        'total_records': total,
        'average_quality': avg_quality,
        'quality_distribution': quality_distribution,
        'field_coverage': field_coverage,
        'validation': validation_stats,
    }

    # 7. 输出
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info(f"管线完成: {total} 条数据, 平均质量 {avg_quality}")
    logger.info(f"质量分布: {quality_distribution}")
    logger.info(f"输出: {output}")
    logger.info(f"报告: {report_path}")

    return deduped, report


if __name__ == '__main__':
    run_pipeline()
