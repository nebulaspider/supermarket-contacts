"""RT-Mart (大润发) 联系方式爬虫"""
import scrapy
from scraper.spiders.base_spider import BaseSupermarketSpider

class RtMartSpider(BaseSupermarketSpider):
    name = 'rt_mart'
    brand_name = 'RT-Mart (大润发)'
    country = 'China'
    city = 'Shanghai'
    address = '上海市黄浦区南京东路61号新黄浦金融大厦'
    website = 'https://www.rt-mart.com.cn'

    def start_requests(self):
        for url in ['https://www.rt-mart.com.cn/about', 'https://www.rt-mart.com.cn/contact']:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)
