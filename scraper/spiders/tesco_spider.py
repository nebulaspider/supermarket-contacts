"""
Tesco 联系方式爬虫
"""
import scrapy
from scraper.spiders.base_spider import BaseSupermarketSpider


class TescoSpider(BaseSupermarketSpider):
    name = 'tesco'
    brand_name = 'Tesco'
    country = 'United Kingdom'
    city = 'Welwyn Garden City'
    address = 'Tesco House, Shire Park, Kestrel Way, Welwyn Garden City, AL7 1GA, UK'
    website = 'https://www.tesco.com'

    def start_requests(self):
        urls = [
            'https://www.tescoplc.com/about-us/',
            'https://www.tescoplc.com/contact-us/',
        ]
        for url in urls:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)
