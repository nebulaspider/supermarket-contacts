#!/usr/bin/env python3
"""
高效B2B获客工具 v2
- 使用DuckDuckGo HTML搜索（不被屏蔽）
- 访问公司官网提取真实邮箱、电话、WhatsApp
"""

import re
import json
import time
import random
import urllib.request
import urllib.parse
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
]

def fetch(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        if resp.status == 200:
            return resp.read().decode('utf-8', errors='ignore')
    except:
        pass
    return None

def ddg_search(query, num_results=15):
    """DuckDuckGo HTML搜索"""
    urls = []
    try:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        html = fetch(url)
        if html:
            # DuckDuckGo HTML结果链接格式
            links = re.findall(r'uddg=([^&"]+)', html)
            for link in links:
                link = urllib.parse.unquote(link)
                if link.startswith('http') and not any(x in link for x in [
                    'duckduckgo.com', 'google.com', 'youtube.com', 'facebook.com',
                    'instagram.com', 'linkedin.com', 'twitter.com', 'pinterest.com',
                    'amazon.com', 'ebay.com', 'walmart.com', 'yelp.com',
                    'yellowpages.com', 'manta.com', 'chamberofcommerce.com',
                    'buzzfile.com', 'reddit.com', 'tiktok.com', 'shopify.com',
                    'aliexpress.com', 'alibaba.com', 'made-in-china.com',
                    'globalsources.com', 'dhgate.com', '1688.com',
                ]):
                    if link not in urls:
                        urls.append(link)
            # 备用：直接提取href
            if not urls:
                direct = re.findall(r'href="(https?://[^"]+)"', html)
                for link in direct:
                    if not any(x in link for x in ['duckduckgo.com', 'google.com', 'gstatic.com']):
                        if link not in urls:
                            urls.append(link)
    except Exception as e:
        print(f"  搜索错误: {e}")
    return urls[:num_results]

def extract_domain(url):
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.replace('www.', '')
    except:
        return url

def extract_contacts(html):
    emails, phones, whatsapp = [], [], []
    if not html:
        return emails, phones, whatsapp

    # 邮箱
    found_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
    for e in found_emails:
        e = e.lower().strip()
        if not any(x in e for x in ['example.com', 'domain.com', 'email.com', 'sentry.io', 'wix.com', 'shopify.com', 'godaddy.com', 'test.com', 'yourdomain', 'placeholder', '.png', '.jpg', '.gif', '.webp', '.svg', 'yoursite.com', 'your-email', 'email@']):
            if e not in emails and len(e) < 80:
                emails.append(e)

    # 电话 - 更严格的匹配，减少误报
    phone_patterns = [
        r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\(\d{3}\)\s*\d{3}[-.\s]\d{4}',
        r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b',
        r'1\s*\(\d{3}\)\s*\d{3}[-.\s]\d{4}',
    ]
    for pattern in phone_patterns:
        for p in re.findall(pattern, html):
            p = p.strip()
            digits = re.sub(r'\D', '', p)
            # 必须是10或11位，且不能全是0/1
            if 10 <= len(digits) <= 11 and not all(d in '01' for d in digits):
                # 排除明显不是电话的（如年份2024、订单号等）
                if not p.startswith('20') and not p.startswith('19') and len(digits) == 10:
                    if p not in phones:
                        phones.append(p)
                elif len(digits) == 11 and digits.startswith('1'):
                    if p not in phones:
                        phones.append(p)

    # WhatsApp
    for pattern in [r'wa\.me/(\d+)', r'whatsapp[^<]{0,50}(\+?\d{10,15})']:
        for w in re.findall(pattern, html, re.IGNORECASE):
            w = str(w).strip()
            if w not in whatsapp and len(w) >= 8:
                whatsapp.append(w)

    # 社交媒体
    social = {}
    social_patterns = {
        'facebook': r'https?://(?:www\.)?facebook\.com/([a-zA-Z0-9._-]+)',
        'instagram': r'https?://(?:www\.)?instagram\.com/([a-zA-Z0-9._-]+)',
        'linkedin': r'https?://(?:www\.)?linkedin\.com/(?:company|in)/([a-zA-Z0-9._-]+)',
        'twitter': r'https?://(?:www\.)?(?:twitter|x)\.com/([a-zA-Z0-9._-]+)',
        'youtube': r'https?://(?:www\.)?youtube\.com/(?:c|channel|@)([a-zA-Z0-9._-]+)',
        'pinterest': r'https?://(?:www\.)?pinterest\.com/([a-zA-Z0-9._-]+)',
    }
    for platform, pattern in social_patterns.items():
        matches = re.findall(pattern, html, re.IGNORECASE)
        for m in matches:
            m = m.strip().rstrip('/')
            if m and m not in ['pages', 'share', 'sharer', 'dialog', 'login', 'signup', 'home', 'tr', 'watch', 'hashtag']:
                if platform not in social:
                    social[platform] = m
                break

    return emails[:5], phones[:5], whatsapp[:3], social

def get_company_name(html, url):
    title_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()
        title = re.sub(r'\s*[|\-–—:].*$', '', title).strip()
        if 3 < len(title) < 80:
            return title
    og_match = re.search(r'og:site_name"\s+content="([^"]+)"', html, re.IGNORECASE)
    if og_match:
        return og_match.group(1).strip()
    return extract_domain(url)

def crawl_company(url, industry, country):
    domain = extract_domain(url)
    print(f"  {domain}...", end=" ", flush=True)

    html = fetch(url)
    if not html:
        print("✗ 无法访问")
        return None

    company_name = get_company_name(html, url)
    emails, phones, whatsapp, social = extract_contacts(html)

    # 尝试contact页面
    if not emails or not phones or not social:
        for path in ['/contact', '/contact-us', '/contact-us/', '/about', '/about-us', '/support', '/wholesale', '/vendor']:
            if len(emails) >= 2 and len(phones) >= 2 and social:
                break
            ch = fetch(url.rstrip('/') + path, timeout=10)
            if ch:
                e2, p2, w2, s2 = extract_contacts(ch)
                for e in e2:
                    if e not in emails: emails.append(e)
                for p in p2:
                    if p not in phones: phones.append(p)
                for w in w2:
                    if w not in whatsapp: whatsapp.append(w)
                for k, v in s2.items():
                    if k not in social: social[k] = v
            time.sleep(random.uniform(0.3, 1))

    # 地址
    address = ''
    addr_match = re.search(r'<address[^>]*>(.*?)</address>', html, re.DOTALL | re.IGNORECASE)
    if addr_match:
        address = re.sub(r'<[^>]+>', ' ', addr_match.group(1)).strip()
        address = re.sub(r'\s+', ' ', address)[:150]

    has_contact = bool(emails or phones or whatsapp)
    quality = min((30 if emails else 0) + (30 if phones else 0) + (20 if whatsapp else 0) + (10 if address else 0) + (10 if company_name != domain else 0) + (10 if social else 0), 100)

    print(f"{'✓' if has_contact else '○'} 邮箱:{len(emails)} 电话:{len(phones)} WA:{len(whatsapp)} 社交:{len(social)}")

    return {
        'company_name': company_name,
        'industry': industry,
        'country': country,
        'website': domain,
        'url': url,
        'email': emails[0] if emails else '',
        'all_emails': emails,
        'phone': phones[0] if phones else '',
        'all_phones': phones,
        'whatsapp': whatsapp[0] if whatsapp else '',
        'social': social,
        'facebook': social.get('facebook', ''),
        'instagram': social.get('instagram', ''),
        'linkedin': social.get('linkedin', ''),
        'twitter': social.get('twitter', ''),
        'youtube': social.get('youtube', ''),
        'address': address,
        'data_quality': quality,
        'source': 'DuckDuckGo + Website',
        'status': '待联系',
    }

def find_leads(industries, country='USA', max_per_industry=8):
    all_leads = []
    for industry in industries:
        print(f"\n{'='*50}")
        print(f"行业: {industry} | {country}")
        print(f"{'='*50}")

        queries = [
            f"{industry} wholesale distributor {country}",
            f"{industry} supplier {country} B2B",
            f"{industry} importer {country} contact",
        ]

        found_urls = []
        for query in queries:
            print(f"\n搜索: {query}")
            urls = ddg_search(query, num_results=12)
            print(f"  找到 {len(urls)} 个网站")
            for u in urls:
                if u not in found_urls:
                    found_urls.append(u)
            time.sleep(random.uniform(2, 4))

        found_urls = found_urls[:max_per_industry]
        print(f"\n爬取 {len(found_urls)} 个网站:")

        for url in found_urls:
            try:
                lead = crawl_company(url, industry, country)
                if lead:
                    all_leads.append(lead)
            except Exception as e:
                print(f"  错误: {e}")
            time.sleep(random.uniform(1, 2.5))

    return all_leads

if __name__ == '__main__':
    import sys
    industries = sys.argv[1].split(',') if len(sys.argv) > 1 else [
        'furniture', 'cosmetics', 'electronics', 'pet supplies',
        'kitchenware', 'sporting goods', 'jewelry', 'home decor',
    ]
    country = sys.argv[2] if len(sys.argv) > 2 else 'USA'
    max_per = int(sys.argv[3]) if len(sys.argv) > 3 else 6

    print(f"🚀 高效获客: {len(industries)}行业 x 每行业{max_per}网站 = 最多{len(industries)*max_per}客户")
    leads = find_leads(industries, country, max_per)

    with open('data/effective_leads.json', 'w', encoding='utf-8') as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)

    with_email = [l for l in leads if l['email']]
    with_phone = [l for l in leads if l['phone']]
    with_wa = [l for l in leads if l['whatsapp']]
    hq = [l for l in leads if l['data_quality'] >= 60]

    print(f"\n{'='*50}")
    print(f"📊 完成! 总客户:{len(leads)} | 邮箱:{len(with_email)} | 电话:{len(with_phone)} | WA:{len(with_wa)} | 高质量:{len(hq)}")
    print(f"{'='*50}")
    for l in sorted(hq, key=lambda x: x['data_quality'], reverse=True)[:10]:
        print(f"\n  [{l['data_quality']}] {l['company_name']} ({l['industry']})")
        print(f"     {l['website']}")
        if l['email']: print(f"     ✉️ {l['email']}")
        if l['phone']: print(f"     📞 {l['phone']}")
        if l['whatsapp']: print(f"     💬 {l['whatsapp']}")
