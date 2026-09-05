"""
Walmart 联系方式爬虫
数据来源：Walmart 官网公开联系页面
"""
import scrapy
from scraper.spiders.base_spider import BaseSupermarketSpider


class WalmartSpider(BaseSupermarketSpider):
    name = 'walmart'
    brand_name = 'Walmart'
    country = 'United States'
    city = 'Bentonville'
    address = '702 SW 8th Street, Bentonville, AR 72716'
    website = 'https://www.walmart.com'

    # 注意：实际抓取时需遵守 Walmart 的 robots.txt
    # 以下为公开联系页面示例
    def start_requests(self):
        urls = [
            'https://corporate.walmart.com/about',
            'https://corporate.walmart.com/contact-us',
        ]
        for url in urls:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)
