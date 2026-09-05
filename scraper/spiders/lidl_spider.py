"""Lidl 联系方式爬虫"""
import scrapy
from scraper.spiders.base_spider import BaseSupermarketSpider

class LidlSpider(BaseSupermarketSpider):
    name = 'lidl'
    brand_name = 'Lidl'
    country = 'Germany'
    city = 'Neckarsulm'
    address = 'Stiftsbergstraße 1, 74172 Neckarsulm, Germany'
    website = 'https://www.lidl.com'

    def start_requests(self):
        for url in ['https://www.lidl.com/about-us', 'https://www.lidl.com/contact']:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)
