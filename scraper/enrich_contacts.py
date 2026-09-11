#!/usr/bin/env python3
"""
联系方式补全脚本
访问有网站但缺邮箱/电话的客户，从官网提取联系方式
"""
import json
import re
import urllib.request
import urllib.error
import ssl
import time
import sys
from html.parser import HTMLParser

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_PATTERN = re.compile(r'(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')

CONTACT_PATHS = [
    '/contact', '/contact-us', '/contact-us/', '/contacts',
    '/about', '/about-us', '/about-us/',
    '/support', '/help', '/customer-service',
    '/',  # 最后试首页
]

INVALID_EMAILS = [
    'example.com', 'test.com', 'domain.com', 'yourdomain',
    'yoursite.com', 'email.com', 'name@email', 'wix.com',
    'sentry.io', 'google.com', 'github.com', 'cloudflare',
    'fontawesome', 'bootstrap', 'jquery', 'cdn.',
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.css', '.js',
    'webmaster@', 'postmaster@', 'noreply@', 'no-reply@',
    'donotreply@', 'mail@example', 'admin@example',
]

def fetch_url(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            if resp.status == 200:
                return resp.read().decode('utf-8', errors='ignore')
    except:
        pass
    return None

def extract_contacts(html):
    if not html:
        return [], []
    
    emails = []
    for m in EMAIL_PATTERN.findall(html):
        email = m.lower().strip()
        if any(inv in email for inv in INVALID_EMAILS):
            continue
        if email not in emails:
            emails.append(email)
    
    phones = []
    for m in PHONE_PATTERN.findall(html):
        phone = m.strip()
        digits = re.sub(r'\D', '', phone)
        if len(digits) >= 10 and phone not in phones:
            phones.append(phone)
    
    return emails, phones

def enrich_lead(lead):
    website = lead.get('website', '').strip()
    if not website:
        return lead
    
    base_url = f"https://{website}"
    found_email = None
    found_phone = None
    
    for path in CONTACT_PATHS:
        url = base_url + path
        html = fetch_url(url)
        if html:
            emails, phones = extract_contacts(html)
            if emails and not found_email:
                found_email = emails[0]
            if phones and not found_phone:
                found_phone = phones[0]
            if found_email and found_phone:
                break
        time.sleep(0.5)  # 礼貌延迟
    
    if found_email and not lead.get('email'):
        lead['email'] = found_email
        print(f"    ✓ 补全邮箱: {found_email}")
    if found_phone and not lead.get('phone'):
        lead['phone'] = found_phone
        print(f"    ✓ 补全电话: {found_phone}")
    
    return lead

def main():
    data_file = 'data/effective_leads.json'
    with open(data_file, 'r') as f:
        leads = json.load(f)
    
    # 找出需要补全的客户（有网站但缺邮箱）
    to_enrich = [l for l in leads if l.get('website') and not l.get('email')]
    print(f"总客户: {len(leads)}, 需要补全邮箱: {len(to_enrich)}")
    
    # 限制数量，避免运行太久
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    to_enrich = to_enrich[:limit]
    print(f"本次补全: {len(to_enrich)} 个\n")
    
    enriched = 0
    for i, lead in enumerate(to_enrich):
        print(f"[{i+1}/{len(to_enrich)}] {lead['company_name'][:40]} ({lead['website']})")
        original_email = lead.get('email')
        original_phone = lead.get('phone')
        lead = enrich_lead(lead)
        if lead.get('email') != original_email or lead.get('phone') != original_phone:
            enriched += 1
    
    # 保存
    with open(data_file, 'w') as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)
    
    has_email = len([l for l in leads if l.get('email')])
    print(f"\n📊 补全完成!")
    print(f"  成功补全: {enriched} 个")
    print(f"  有邮箱: {has_email}/{len(leads)} ({has_email/len(leads)*100:.0f}%)")

if __name__ == '__main__':
    main()
