#!/usr/bin/env python3
"""
目录爬虫运行脚本（由 GitHub Actions 调用）
从环境变量读取参数，运行目录爬虫并输出结果。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from directory_runner import run_directory_crawl


def main():
    industries_str = os.environ.get('INDUSTRIES', 'general,retail,electronics,furniture,cosmetics')
    max_companies = int(os.environ.get('MAX_COMPANIES', '80'))
    country = os.environ.get('COUNTRY', '')

    industries = [i.strip() for i in industries_str.split(',') if i.strip()]

    print(f"行业: {industries}")
    print(f"国家: {country or '全球'}")
    print(f"最大数量: {max_companies}")
    print("=" * 50)

    data = run_directory_crawl(
        industries=industries,
        country=country,
        max_companies=max_companies,
        extract_contacts=True,
        output_path='../data/clients.directory.json',
    )

    email_count = sum(1 for d in data if d.get('email'))
    phone_count = sum(1 for d in data if d.get('phone'))

    print(f"\n目录爬虫完成: {len(data)} 条")
    print(f"有邮箱: {email_count}")
    print(f"有电话: {phone_count}")


if __name__ == '__main__':
    main()
