"""Target 联系方式爬虫"""
import scrapy
from scraper.spiders.base_spider import BaseSupermarketSpider

class TargetSpider(BaseSupermarketSpider):
    name = 'target'
    brand_name = 'Target'
    country = 'United States'
    city = 'Minneapolis'
    address = '1000 Nicollet Mall, Minneapolis, MN 55403, USA'
    website = 'https://www.target.com'

    def start_requests(self):
        for url in ['https://corporate.target.com/contact-us', 'https://corporate.target.com/about/']:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)
