"""
Carrefour 联系方式爬虫
数据来源：Carrefour 集团官网公开页面
"""
import scrapy
from scraper.spiders.base_spider import BaseSupermarketSpider


class CarrefourSpider(BaseSupermarketSpider):
    name = 'carrefour'
    brand_name = 'Carrefour'
    country = 'France'
    city = 'Massy'
    address = '119 avenue de France, 91039 Massy Cedex, France'
    website = 'https://www.carrefour.com'

    def start_requests(self):
        urls = [
            'https://www.carrefour.com/en/who-we-are',
            'https://www.carrefour.com/en/contact',
        ]
        for url in urls:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)
