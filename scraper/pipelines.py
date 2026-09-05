"""
数据管道：清洗、去重、计算数据完整度、输出 JSON/CSV
"""
import json
import os
import re
from datetime import datetime, timezone
from itemadapter import ItemAdapter


class DataCleaningPipeline:
    """清洗字段：去除空白、标准化电话/邮箱格式。"""

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # 去除所有字符串字段的首尾空白
        for key, value in adapter.items():
            if isinstance(value, str):
                adapter[key] = value.strip()

        # 标准化邮箱（小写）
        if adapter.get('email'):
            adapter['email'] = adapter['email'].lower()

        # 标准化电话：去除多余空格和横线（保留 + 号）
        if adapter.get('phone'):
            phone = re.sub(r'[\s\-]', '', adapter['phone'])
            adapter['phone'] = phone

        # 标准化 WhatsApp
        if adapter.get('whatsapp'):
            wa = re.sub(r'[\s\-]', '', adapter['whatsapp'])
            adapter['whatsapp'] = wa

        # 确保 URL 带协议
        for url_field in ['website', 'linkedin', 'facebook', 'twitter', 'instagram', 'youtube']:
            if adapter.get(url_field) and not adapter[url_field].startswith(('http://', 'https://')):
                adapter[url_field] = 'https://' + adapter[url_field]

        return item


class DeduplicationPipeline:
    """基于公司名称+国家去重。"""

    def __init__(self):
        self.seen = set()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        key = (
            adapter.get('company_name', '').lower(),
            adapter.get('country', '').lower(),
        )
        if key in self.seen:
            raise DropItem(f"重复数据: {adapter.get('company_name')}")
        self.seen.add(key)
        return item


class DataQualityPipeline:
    """计算数据完整度评分（0-100），便于前端筛选高质量数据。"""

    # 各字段权重
    FIELD_WEIGHTS = {
        'company_name': 15,
        'country': 10,
        'city': 5,
        'address': 5,
        'website': 10,
        'email': 15,
        'phone': 15,
        'whatsapp': 5,
        'wechat': 5,
        'linkedin': 10,
        'facebook': 2,
        'twitter': 1,
        'instagram': 1,
        'youtube': 1,
    }

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        score = 0
        for field, weight in self.FIELD_WEIGHTS.items():
            if adapter.get(field):
                score += weight
        adapter['data_quality'] = min(score, 100)
        adapter['scraped_at'] = datetime.now(timezone.utc).isoformat()
        return item


class JsonExportPipeline:
    """导出为结构化 JSON 文件（兼容前端读取）。"""

    def __init__(self):
        self.items = []

    def process_item(self, item, spider):
        self.items.append(ItemAdapter(item).asdict())
        return item

    def close_spider(self, spider):
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'clients.json')

        # 按 data_quality 降序排列
        self.items.sort(key=lambda x: x.get('data_quality', 0), reverse=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.items, f, ensure_ascii=False, indent=2)

        spider.logger.info(f"已导出 {len(self.items)} 条数据到 {output_path}")


# 需要导入 DropItem
from scrapy.exceptions import DropItem
