"""
Scrapy 全局配置
- 遵守 robots.txt
- 设置请求延迟，避免被封
- 支持代理池（通过环境变量配置）
"""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_NAME = 'supermarket_contacts'

SPIDER_MODULES = ['scraper.spiders']
NEWSPIDER_MODULE = 'scraper.spiders'

# 遵守 robots.txt（合规关键）
ROBOTSTXT_OBEY = True

# 请求延迟（秒）—— 对同一域名的请求间隔
DOWNLOAD_DELAY = 3.0
RANDOMIZE_DOWNLOAD_DELAY = True

# 并发控制
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 2
CONCURRENT_REQUESTS_PER_IP = 2

# 禁用 cookies（减少被追踪风险）
COOKIES_ENABLED = False

# User-Agent 轮换
USER_AGENT_LIST = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
]

# 默认 User-Agent
USER_AGENT = USER_AGENT_LIST[0]

# 下载器中间件
DOWNLOADER_MIDDLEWARES = {
    'scraper.middlewares.RandomUserAgentMiddleware': 400,
    'scraper.middlewares.ProxyMiddleware': 410,
}

# 代理池配置（可选，通过环境变量传入代理 API）
# 格式：http://proxy-api.example.com/get?num=1
PROXY_API_URL = os.getenv('PROXY_API_URL', '')
PROXY_ENABLED = bool(PROXY_API_URL)

# 数据输出
FEEDS = {
    '../data/clients.json': {
        'format': 'json',
        'encoding': 'utf-8',
        'indent': 2,
        'overwrite': True,
    },
}

# 日志
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'

# 自动限速（AutoThrottle）—— 根据服务器响应动态调整延迟
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2.0
AUTOTHROTTLE_MAX_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# HTTP 缓存（开发调试用，生产环境关闭）
HTTPCACHE_ENABLED = False
HTTPCACHE_EXPIRATION_SECS = 86400
HTTPCACHE_DIR = 'httpcache'
