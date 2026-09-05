"""Kroger 联系方式爬虫"""
import scrapy
from scraper.spiders.base_spider import BaseSupermarketSpider

class KrogerSpider(BaseSupermarketSpider):
    name = 'kroger'
    brand_name = 'Kroger'
    country = 'United States'
    city = 'Cincinnati'
    address = '1014 Vine Street, Cincinnati, OH 45202, USA'
    website = 'https://www.kroger.com'

    def start_requests(self):
        for url in ['https://www.kroger.com/contactus', 'https://www.thekrogerco.com/about-us/']:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)
