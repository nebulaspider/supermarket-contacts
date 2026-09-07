"""
Facebook 公开主页数据提取器
从 Facebook 公司主页提取公开信息：公司简介、联系方式、关注者数、地址等。
注意：Facebook 有严格的反爬机制，此模块使用公开页面解析，可能需要代理。
合规：仅提取公开的企业商务信息，不抓取个人隐私数据。
"""
import json
import logging
import re
from typing import Dict, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class FacebookExtractor:
    """从 Facebook 公开主页提取公司信息"""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = None

    def _get_session(self):
        if self.session is None:
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': (
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Safari/537.36'
                ),
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'en-US,en;q=0.9',
            })
        return self.session

    def extract(self, facebook_url: str) -> Dict[str, str]:
        """
        从 Facebook 主页提取公开信息。
        返回: about, email, phone, website, followers, address, category
        """
        result = {
            'fb_about': '',
            'fb_email': '',
            'fb_phone': '',
            'fb_website': '',
            'fb_followers': '',
            'fb_address': '',
            'fb_category': '',
        }

        if not facebook_url:
            return result

        try:
            session = self._get_session()
            resp = session.get(facebook_url, timeout=self.timeout, allow_redirects=True)
            if resp.status_code != 200:
                logger.warning(f"Facebook 页面访问失败 {facebook_url}: {resp.status_code}")
                return result

            html = resp.text

            # 提取邮箱
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
            if emails:
                # 过滤掉 Facebook 内部邮箱
                valid = [e for e in emails if 'facebook' not in e.lower() and 'fb.com' not in e.lower()]
                if valid:
                    result['fb_email'] = valid[0]

            # 提取电话
            phones = re.findall(r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]', html)
            if phones:
                result['fb_phone'] = phones[0]

            # 提取网站
            websites = re.findall(r'https?://(?!www\.facebook\.com|facebook\.com)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
            if websites:
                result['fb_website'] = websites[0]

            # 提取关注者数（从页面元数据）
            follower_match = re.search(r'(\d[\d,.KM]*)\s*(?:people|followers|likes)', html, re.IGNORECASE)
            if follower_match:
                result['fb_followers'] = follower_match.group(1)

            # 提取公司简介（从 meta description）
            desc_match = re.search(r'<meta name="description" content="([^"]+)"', html)
            if desc_match:
                result['fb_about'] = desc_match.group(1)[:200]

            # 提取分类
            cat_match = re.search(r'"category":"([^"]+)"', html)
            if cat_match:
                result['fb_category'] = cat_match.group(1)

            logger.info(f"Facebook 提取成功: {facebook_url} -> email={bool(result['fb_email'])}, phone={bool(result['fb_phone'])}")

        except Exception as e:
            logger.warning(f"Facebook 提取失败 {facebook_url}: {e}")

        return result

    def find_facebook_page(self, company_name: str) -> Optional[str]:
        """通过搜索引擎查找公司的 Facebook 主页"""
        try:
            import requests
            from bs4 import BeautifulSoup

            session = self._get_session()
            search_url = f"https://www.google.com/search?q={company_name.replace(' ', '+')}+facebook+page"
            resp = session.get(search_url, timeout=self.timeout)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'facebook.com' in href and '/pages/' not in href:
                    # 提取真实 URL
                    if href.startswith('/url?q='):
                        href = href.split('/url?q=')[1].split('&')[0]
                    return href
        except Exception as e:
            logger.warning(f"查找 Facebook 页面失败 {company_name}: {e}")
        return None
