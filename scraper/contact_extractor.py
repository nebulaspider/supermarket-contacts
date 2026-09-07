"""
官网联系方式提取器
给定公司官网 URL，自动访问并提取邮箱、电话、社交链接。
纯免费方案，用 requests + BeautifulSoup。
"""
import logging
import re
import time
from typing import Dict, Optional, Set
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

# 邮箱正则
EMAIL_RE = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
)
# 电话正则（国际格式）
PHONE_RE = re.compile(
    r'(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}'
)
# 社交平台 URL 正则
SOCIAL_PATTERNS = {
    'linkedin': re.compile(r'https?://(?:www\.)?linkedin\.com/(?:company|in)/[\w-]+', re.I),
    'facebook': re.compile(r'https?://(?:www\.)?facebook\.com/[\w.-]+', re.I),
    'twitter': re.compile(r'https?://(?:www\.)?(?:twitter|x)\.com/[\w]+', re.I),
    'instagram': re.compile(r'https?://(?:www\.)?instagram\.com/[\w.]+', re.I),
    'youtube': re.compile(r'https?://(?:www\.)?youtube\.com/(?:c|channel|@)/[\w-]+', re.I),
}

# 常见的联系页面路径
CONTACT_PATHS = [
    '/contact', '/contact-us', '/contactus', '/contacts',
    '/about', '/about-us', '/aboutus',
    '/imprint', '/impressum', '/legal',
    '/support', '/help',
]

# 需要跳过的邮箱（无效的）
INVALID_EMAILS = {
    'example.com', 'domain.com', 'email.com', 'test.com',
    'yourdomain.com', 'company.com', 'mail.com',
}


class ContactExtractor:
    """从公司官网提取联系方式"""

    def __init__(self, timeout: int = 15, request_delay: float = 1.5):
        self.timeout = timeout
        self.request_delay = request_delay
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
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            })
        return self.session

    def extract(self, website: str) -> Dict[str, str]:
        """
        从公司官网提取联系方式。
        返回字典: email, phone, linkedin, facebook, twitter, instagram, youtube
        """
        result = {
            'email': '', 'phone': '',
            'linkedin': '', 'facebook': '', 'twitter': '',
            'instagram': '', 'youtube': '',
        }

        if not website:
            return result

        # 规范化 URL
        if not website.startswith('http'):
            website = 'https://' + website
        website = website.rstrip('/')

        try:
            # 1. 抓取首页
            homepage_html = self._fetch(website)
            if not homepage_html:
                return result

            self._extract_from_html(homepage_html, website, result)

            # 2. 如果首页没找到邮箱，尝试联系页面
            if not result['email'] or not result['phone']:
                for path in CONTACT_PATHS:
                    contact_url = website + path
                    contact_html = self._fetch(contact_url)
                    if contact_html:
                        self._extract_from_html(contact_html, contact_url, result)
                        if result['email'] and result['phone']:
                            break

        except Exception as e:
            logger.warning(f"提取联系方式失败 {website}: {e}")

        return result

    def _fetch(self, url: str) -> Optional[str]:
        try:
            session = self._get_session()
            resp = session.get(url, timeout=self.timeout, allow_redirects=True)
            if resp.status_code != 200:
                return None
            # 确保是 HTML
            content_type = resp.headers.get('content-type', '')
            if 'html' not in content_type and 'text' not in content_type:
                return None
            time.sleep(self.request_delay)
            return resp.text
        except Exception:
            return None

    def _extract_from_html(self, html: str, base_url: str, result: Dict[str, str]):
        """从 HTML 中提取联系方式"""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')

        # 提取邮箱
        if not result['email']:
            emails = self._extract_emails(soup, html)
            if emails:
                result['email'] = emails[0]

        # 提取电话
        if not result['phone']:
            phone = self._extract_phone(soup, html)
            if phone:
                result['phone'] = phone

        # 提取社交链接
        for platform, pattern in SOCIAL_PATTERNS.items():
            if not result[platform]:
                link = self._extract_social(soup, pattern, base_url)
                if link:
                    result[platform] = link

    def _extract_emails(self, soup, html: str) -> list:
        """提取邮箱地址"""
        emails = set()

        # 从 mailto 链接提取
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('mailto:'):
                email = href[7:].split('?')[0].strip()
                if self._valid_email(email):
                    emails.add(email)

        # 从文本中正则提取
        for match in EMAIL_RE.findall(html):
            if self._valid_email(match):
                emails.add(match)

        return sorted(emails)

    @staticmethod
    def _valid_email(email: str) -> bool:
        """验证邮箱是否有效"""
        email = email.lower().strip()
        if not email or '@' not in email:
            return False
        domain = email.split('@')[-1]
        if domain in INVALID_EMAILS:
            return False
        # 跳过图片扩展名
        if any(email.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']):
            return False
        return True

    def _extract_phone(self, soup, html: str) -> str:
        """提取电话号码"""
        # 从 tel 链接提取
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('tel:'):
                phone = href[4:].strip()
                if len(phone) >= 7:
                    return phone

        # 从包含电话关键词的元素提取
        phone_keywords = ['phone', 'tel', 'telephone', 'fax', 'mobile', 'contact number']
        for el in soup.find_all(['p', 'div', 'span', 'li', 'address']):
            text = el.get_text()
            if any(kw in text.lower() for kw in phone_keywords):
                match = PHONE_RE.search(text)
                if match:
                    phone = match.group().strip()
                    digits = re.sub(r'\D', '', phone)
                    if 7 <= len(digits) <= 15:
                        return phone

        return ''

    def _extract_social(self, soup, pattern: re.Pattern, base_url: str) -> str:
        """提取社交媒体链接"""
        # 从所有链接中找
        for a in soup.find_all('a', href=True):
            href = a['href']
            if pattern.match(href):
                return href
            # 相对路径转绝对
            if href.startswith('/'):
                full_url = urljoin(base_url, href)
                if pattern.match(full_url):
                    return full_url
        return ''
