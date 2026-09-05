"""
基础爬虫类：提供通用的联系方式提取逻辑。
所有品牌爬虫继承此类，只需定义 start_urls 和品牌元数据。

提取策略：
1. 优先从官网 "Contact Us" / "About" 页面提取
2. 使用正则匹配邮箱、电话
3. 从页面 meta 标签、footer 中提取社交媒体链接
4. WhatsApp/微信 通常需要手动补充或第三方 API
"""
import re
import scrapy
from bs4 import BeautifulSoup
from scraper.items import SupermarketContactItem


class BaseSupermarketSpider(scrapy.Spider):
    """超市联系方式爬虫基类。"""

    # 子类需覆盖
    brand_name = ''
    country = ''
    city = ''
    address = ''
    website = ''

    # 邮箱正则
    EMAIL_PATTERN = re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    )

    # 电话正则（国际格式）
    PHONE_PATTERN = re.compile(
        r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}'
    )

    # 社交媒体 URL 正则
    SOCIAL_PATTERNS = {
        'linkedin': re.compile(r'https?://(?:www\.)?linkedin\.com/(?:company|school)/[\w-]+', re.I),
        'facebook': re.compile(r'https?://(?:www\.)?facebook\.com/[\w.-]+', re.I),
        'twitter': re.compile(r'https?://(?:www\.)?(?:twitter|x)\.com/[\w.-]+', re.I),
        'instagram': re.compile(r'https?://(?:www\.)?instagram\.com/[\w.-]+', re.I),
        'youtube': re.compile(r'https?://(?:www\.)?youtube\.com/(?:c|channel|@)/[\w.-]+', re.I),
    }

    def parse(self, response):
        """解析页面，提取联系方式。"""
        soup = BeautifulSoup(response.text, 'lxml')
        text = soup.get_text()

        item = SupermarketContactItem()
        item['company_name'] = self.brand_name
        item['country'] = self.country
        item['city'] = self.city
        item['address'] = self.address
        item['website'] = self.website
        item['source_url'] = response.url

        # 提取邮箱
        emails = self.EMAIL_PATTERN.findall(text)
        # 过滤常见的无效邮箱
        invalid = {'example.com', 'domain.com', 'email.com', 'test.com'}
        valid_emails = [e for e in emails if e.split('@')[-1].lower() not in invalid]
        if valid_emails:
            item['email'] = valid_emails[0]

        # 提取电话
        phones = self.PHONE_PATTERN.findall(text)
        if phones:
            # 取最长的（通常是完整国际号码）
            item['phone'] = max(phones, key=len)

        # 提取社交媒体链接
        for field, pattern in self.SOCIAL_PATTERNS.items():
            matches = pattern.findall(response.text)
            if matches:
                item[field] = matches[0]

        # WhatsApp：从页面中查找 wa.me 或 whatsapp.com 链接
        wa_pattern = re.compile(r'https?://(?:wa\.me|(?:www\.)?whatsapp\.com)/(?:send\?phone=)?(\d+)', re.I)
        wa_matches = wa_pattern.findall(response.text)
        if wa_matches:
            item['whatsapp'] = '+' + wa_matches[0]

        # 微信：查找 weixin.qq.com 或 微信号文本
        wechat_pattern = re.compile(r'(?:微信号|WeChat|weixin)[：:\s]*([a-zA-Z][a-zA-Z0-9_-]{5,19})', re.I)
        wechat_matches = wechat_pattern.findall(text)
        if wechat_matches:
            item['wechat'] = wechat_matches[0]

        yield item

    def get_contact_page_urls(self, base_url):
        """
        生成常见的联系页面 URL 列表。
        子类可在 start_requests 中调用此方法。
        """
        paths = [
            '/contact', '/contact-us', '/contactus', '/contacts',
            '/about', '/about-us', '/aboutus', '/company',
            '/help', '/help-center', '/customer-service',
            '/en/contact', '/en/contact-us',
        ]
        return [base_url.rstrip('/') + p for p in paths]
