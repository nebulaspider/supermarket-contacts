"""7-Eleven 联系方式爬虫"""
import scrapy
from scraper.spiders.base_spider import BaseSupermarketSpider

class SevenElevenSpider(BaseSupermarketSpider):
    name = 'seven_eleven'
    brand_name = '7-Eleven'
    country = 'Japan'
    city = 'Tokyo'
    address = '1-17-1 Konan, Minato-ku, Tokyo 108-0075, Japan'
    website = 'https://www.7-eleven.com'

    def start_requests(self):
        for url in ['https://www.7-eleven.com/contact-us', 'https://corp.7-eleven.com/about']:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)
