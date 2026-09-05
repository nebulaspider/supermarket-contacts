"""
统一运行入口：全自动化管线

管线流程：
  1. auto_discover  —— 自动发现新品牌
  2. scrapy crawl   —— 多品牌并行抓取
  3. data_manager   —— 合并、去重、验证、评分、导出

用法：
  python scraper/run.py                  # 运行完整管线
  python scraper/run.py --pipeline       # 同上（完整管线）
  python scraper/run.py --scrape-only    # 只运行爬虫
  python scraper/run.py --discover-only  # 只运行自动发现
  python scraper/run.py --manage-only    # 只运行数据管理
  python scraper/run.py --spider walmart # 只运行指定爬虫
  python scraper/run.py --list           # 列出所有可用爬虫
"""
import sys
import os
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger('run')

# 所有可用爬虫
ALL_SPIDERS = [
    'walmart', 'costco', 'kroger', 'target',
    'carrefour', 'tesco', 'aldi', 'lidl', 'metro', 'spar',
    'seven_eleven', 'aeon', 'lotte_mart', 'rt_mart',
]


def run_discover():
    """步骤1：自动发现新品牌。"""
    logger.info("=" * 50)
    logger.info("步骤 1/3: 自动发现新品牌")
    logger.info("=" * 50)
    try:
        from scraper.auto_discover import discover_new_brands
        new_brands = discover_new_brands()
        logger.info(f"自动发现完成: {len(new_brands)} 个新品牌候选")
        return True
    except Exception as e:
        logger.error(f"自动发现失败: {e}")
        return False


def run_scrape(spider_name=None):
    """步骤2：运行爬虫。"""
    logger.info("=" * 50)
    logger.info("步骤 2/3: 数据抓取")
    logger.info("=" * 50)

    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    settings = get_project_settings()
    settings.set('ITEM_PIPELINES', {
        'scraper.pipelines.DataCleaningPipeline': 100,
        'scraper.pipelines.DeduplicationPipeline': 200,
        'scraper.pipelines.DataQualityPipeline': 300,
    })
    # 爬虫输出到临时文件，由 data_manager 合并
    settings.set('FEEDS', {
        '../data/clients.scraped.json': {
            'format': 'json', 'encoding': 'utf-8', 'indent': 2, 'overwrite': True,
        },
    })

    process = CrawlerProcess(settings)
    spiders = [spider_name] if spider_name else ALL_SPIDERS

    for s in spiders:
        if s not in ALL_SPIDERS:
            logger.error(f"未找到爬虫: {s}")
            logger.info(f"可用: {', '.join(ALL_SPIDERS)}")
            return False
        process.crawl(s)

    logger.info(f"运行爬虫: {', '.join(spiders)}")
    process.start()
    logger.info("爬虫运行完毕")
    return True


def run_data_manager():
    """步骤3：数据管理（合并、去重、验证、评分、导出）。"""
    logger.info("=" * 50)
    logger.info("步骤 3/3: 数据管理与导出")
    logger.info("=" * 50)
    try:
        from scraper.data_manager import run_pipeline
        data, report = run_pipeline()
        logger.info(f"数据管理完成: {len(data)} 条记录, 平均质量 {report['average_quality']}")
        return True
    except Exception as e:
        logger.error(f"数据管理失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='SupermarketIQ 全自动化管线')
    parser.add_argument('--pipeline', action='store_true', help='运行完整管线（默认）')
    parser.add_argument('--scrape-only', action='store_true', help='只运行爬虫')
    parser.add_argument('--discover-only', action='store_true', help='只运行自动发现')
    parser.add_argument('--manage-only', action='store_true', help='只运行数据管理')
    parser.add_argument('--spider', type=str, help='只运行指定爬虫')
    parser.add_argument('--list', action='store_true', help='列出所有可用爬虫')
    args = parser.parse_args()

    if args.list:
        print('可用爬虫列表：')
        for s in ALL_SPIDERS:
            print(f'  - {s}')
        return

    if args.discover_only:
        run_discover()
        return

    if args.scrape_only:
        run_scrape(args.spider)
        return

    if args.manage_only:
        run_data_manager()
        return

    # 默认：完整管线
    logger.info("启动 SupermarketIQ 全自动化管线")
    logger.info(f"共 {len(ALL_SPIDERS)} 个品牌爬虫待运行")

    # 步骤1：自动发现（非关键路径，失败不中断）
    run_discover()

    # 步骤2：爬虫抓取
    scrape_ok = run_scrape(args.spider)

    # 步骤3：数据管理（即使爬虫部分失败也运行，用现有数据合并）
    run_data_manager()

    logger.info("=" * 50)
    logger.info("全自动化管线执行完毕")
    logger.info("数据已输出到 data/clients.json")
    logger.info("质量报告: data/quality_report.json")
    logger.info("=" * 50)


if __name__ == '__main__':
    main()
