"""Lotte Mart (乐天玛特) 联系方式爬虫"""
import scrapy
from scraper.spiders.base_spider import BaseSupermarketSpider

class LotteMartSpider(BaseSupermarketSpider):
    name = 'lotte_mart'
    brand_name = 'Lotte Mart (乐天玛特)'
    country = 'South Korea'
    city = 'Seoul'
    address = '267, Olympic-ro, Songpa-gu, Seoul, South Korea'
    website = 'https://www.lottemart.com'

    def start_requests(self):
        for url in ['https://www.lottemart.com/about', 'https://www.lottemart.com/contact']:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)
