"""Aeon (永旺) 联系方式爬虫"""
import scrapy
from scraper.spiders.base_spider import BaseSupermarketSpider

class AeonSpider(BaseSupermarketSpider):
    name = 'aeon'
    brand_name = 'Aeon (永旺)'
    country = 'Japan'
    city = 'Chiba'
    address = '2-1-1 Takashima, Chiba-shi, Chiba 260-8555, Japan'
    website = 'https://www.aeon.info'

    def start_requests(self):
        for url in ['https://www.aeon.info/company/', 'https://www.aeon.info/contact/']:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)
