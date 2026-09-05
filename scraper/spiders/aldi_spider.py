"""
Aldi 联系方式爬虫
"""
import scrapy
from scraper.spiders.base_spider import BaseSupermarketSpider


class AldiSpider(BaseSupermarketSpider):
    name = 'aldi'
    brand_name = 'Aldi'
    country = 'Germany'
    city = 'Essen'
    address = 'Hohe Straße 110, 45138 Essen, Germany'
    website = 'https://www.aldi.com'

    def start_requests(self):
        urls = [
            'https://www.aldi.com/en/about-aldi/',
            'https://www.aldi.com/en/service/contact/',
        ]
        for url in urls:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)
