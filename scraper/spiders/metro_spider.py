"""Metro AG 联系方式爬虫"""
import scrapy
from scraper.spiders.base_spider import BaseSupermarketSpider

class MetroSpider(BaseSupermarketSpider):
    name = 'metro'
    brand_name = 'Metro AG'
    country = 'Germany'
    city = 'Düsseldorf'
    address = 'Metro-Straße 1, 40235 Düsseldorf, Germany'
    website = 'https://www.metro.de'

    def start_requests(self):
        for url in ['https://www.metro.de/unternehmen/ueber-uns', 'https://www.metro.de/kontakt']:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)
