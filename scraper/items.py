"""
Scrapy Item 定义：全球超市客户联系方式数据结构
所有字段均为公开企业商务信息，不涉及个人隐私。
"""
import scrapy


class SupermarketContactItem(scrapy.Item):
    # ===== 基本信息 =====
    company_name = scrapy.Field()       # 公司名称
    country = scrapy.Field()            # 国家/地区
    city = scrapy.Field()               # 城市
    address = scrapy.Field()            # 地址
    website = scrapy.Field()            # 官网

    # ===== 行业与企业属性（LinkedIn 式分类）=====
    industry = scrapy.Field()           # 行业：零售/批发/便利店/会员仓储/折扣店/电商/百货
    company_size = scrapy.Field()       # 企业规模：1-50/51-200/201-500/501-1000/1001-5000/5001-10000/10000+
    founded_year = scrapy.Field()       # 成立年份
    parent_company = scrapy.Field()     # 母公司/集团
    store_count = scrapy.Field()        # 门店数量
    product_categories = scrapy.Field() # 主营品类：食品/日用品/家电/服装/生鲜等

    # ===== 关键联系人（采购决策链）=====
    contact_person = scrapy.Field()     # 联系人姓名（企业公开的采购负责人）
    position = scrapy.Field()           # 职位：采购经理/供应链总监/商品总监/买手/进口经理
    department = scrapy.Field()         # 部门：采购部/供应链部/商品部/国际采购部
    contact_email = scrapy.Field()      # 联系人直邮（企业公开邮箱）
    contact_phone = scrapy.Field()      # 联系人直线电话
    contact_linkedin = scrapy.Field()   # 联系人 LinkedIn 主页（公开 URL）

    # ===== 公司联系方式 =====
    email = scrapy.Field()              # 公司总邮箱
    phone = scrapy.Field()              # 公司总机
    procurement_email = scrapy.Field()  # 采购部专用邮箱
    whatsapp = scrapy.Field()           # WhatsApp 号码
    wechat = scrapy.Field()             # 微信号/公众号
    linkedin = scrapy.Field()           # 公司 LinkedIn 主页

    # 其他社交媒体
    facebook = scrapy.Field()
    twitter = scrapy.Field()
    instagram = scrapy.Field()
    youtube = scrapy.Field()

    # 元数据
    source_url = scrapy.Field()         # 数据来源页面
    scraped_at = scrapy.Field()         # 抓取时间
    data_quality = scrapy.Field()       # 数据完整度评分 (0-100)
