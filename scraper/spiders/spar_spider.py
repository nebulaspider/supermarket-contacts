"""SPAR 联系方式爬虫"""
import scrapy
from scraper.spiders.base_spider import BaseSupermarketSpider

class SparSpider(BaseSupermarketSpider):
    name = 'spar'
    brand_name = 'SPAR'
    country = 'Netherlands'
    city = 'Amsterdam'
    address = 'SPAR International, Hoogoorddreef 9, 1101 BA Amsterdam, Netherlands'
    website = 'https://www.spar-international.com'

    def start_requests(self):
        for url in ['https://www.spar-international.com/about-spar', 'https://www.spar-international.com/contact']:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)
