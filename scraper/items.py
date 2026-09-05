"""
Scrapy Item 定义：全球超市客户联系方式数据结构
所有字段均为公开企业商务信息，不涉及个人隐私。
"""
import scrapy


class SupermarketContactItem(scrapy.Item):
    # 基本信息
    company_name = scrapy.Field()       # 公司名称
    country = scrapy.Field()            # 国家/地区
    city = scrapy.Field()               # 城市
    address = scrapy.Field()            # 地址
    website = scrapy.Field()            # 官网

    # 联系方式
    email = scrapy.Field()              # 联系邮箱（企业公开邮箱）
    phone = scrapy.Field()              # 联系电话
    whatsapp = scrapy.Field()           # WhatsApp 号码
    wechat = scrapy.Field()             # 微信号/公众号
    linkedin = scrapy.Field()           # LinkedIn 主页

    # 其他社交媒体
    facebook = scrapy.Field()
    twitter = scrapy.Field()
    instagram = scrapy.Field()
    youtube = scrapy.Field()

    # 元数据
    source_url = scrapy.Field()         # 数据来源页面
    scraped_at = scrapy.Field()         # 抓取时间
    data_quality = scrapy.Field()       # 数据完整度评分 (0-100)
