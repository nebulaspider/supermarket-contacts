#!/usr/bin/env python3
"""
合并目录爬虫数据与现有数据（由 GitHub Actions 调用）
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from directory_runner import merge_with_existing


def main():
    directory_file = '../data/clients.directory.json'
    existing_file = '../data/clients.json'

    if not os.path.exists(directory_file):
        print('无目录数据，跳过合并')
        return

    with open(directory_file, 'r', encoding='utf-8') as f:
        dir_data = json.load(f)

    merged = merge_with_existing(dir_data, existing_file)

    with open(existing_file, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f'合并后: {len(merged)} 条（新增目录数据 {len(dir_data)} 条）')


if __name__ == '__main__':
    main()
