"""
Costco 联系方式爬虫
"""
import scrapy
from scraper.spiders.base_spider import BaseSupermarketSpider


class CostcoSpider(BaseSupermarketSpider):
    name = 'costco'
    brand_name = 'Costco'
    country = 'United States'
    city = 'Issaquah'
    address = '999 Lake Drive, Issaquah, WA 98027, USA'
    website = 'https://www.costco.com'

    def start_requests(self):
        urls = [
            'https://www.costco.com/contact-us.html',
            'https://investor.costco.com/overview/default.aspx',
        ]
        for url in urls:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)
