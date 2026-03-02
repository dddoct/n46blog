#!/usr/bin/env python3
"""
乃木坂46博客图片爬虫 - 主程序

使用方法:
    python main.py crawl          # 爬取博客列表和图片信息
    python main.py download       # 下载所有图片
    python main.py stats          # 显示统计信息
    python main.py full           # 完整流程：爬取+下载

选项:
    --pages N                     # 限制爬取页数
    --author "成员名"              # 只爬取特定成员
    --start-date YYYY-MM-DD       # 开始日期
    --end-date YYYY-MM-DD         # 结束日期
"""

import argparse
import asyncio
import sys
from datetime import datetime

from config import ensure_dirs
from scraper import N46Scraper
from database import Database


def print_banner():
    """打印程序横幅"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║           紫团 博客图片爬虫 v1.2                      ║
    ║           Purple Group Blog Image Crawler                   ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def cmd_crawl(args):
    """爬取博客列表命令"""
    print("【模式】爬取博客列表和图片信息")
    print(f"【参数】页数限制: {args.pages or '无限制'}")
    
    ensure_dirs()
    
    with N46Scraper() as scraper:
        total = scraper.crawl_blog_list(
            start_page=1,
            max_pages=args.pages
        )
    
    print(f"\n爬取完成！共获取 {total} 篇博客")


def cmd_download(args):
    """下载图片命令"""
    print("【模式】下载图片")
    
    with N46Scraper() as scraper:
        asyncio.run(scraper.download_images())
    
    print("\n下载完成！")


def cmd_stats(args):
    """显示统计信息命令"""
    print("【模式】统计信息")
    
    with Database() as db:
        stats = db.get_stats()
    
    print("\n" + "="*50)
    print("📊 数据统计")
    print("="*50)
    print(f"  博客总数:     {stats['total_blogs']}")
    print(f"  成员数:       {stats['total_authors']}")
    print(f"  图片总数:     {stats['total_images']}")
    print(f"  已下载图片:   {stats['downloaded_images']}")
    print(f"  待下载图片:   {stats['total_images'] - stats['downloaded_images']}")
    print("="*50)


def cmd_full(args):
    """完整流程命令"""
    print("【模式】完整流程（爬取 + 下载）")
    
    ensure_dirs()
    
    with N46Scraper() as scraper:
        # 第一步：爬取博客
        print("\n>>> 第一步：爬取博客列表")
        total = scraper.crawl_blog_list(
            start_page=1,
            max_pages=args.pages
        )
        
        # 第二步：下载图片
        print("\n>>> 第二步：下载图片")
        asyncio.run(scraper.download_images())
    
    print("\n全部完成！")


def cmd_export(args):
    """导出数据命令"""
    import json
    from config import DATA_DIR
    import os
    
    print("【模式】导出数据")
    
    with Database() as db:
        # 导出博客数据
        db.cursor.execute('SELECT * FROM blogs ORDER BY publish_date DESC')
        blogs = db.cursor.fetchall()
        
        blog_list = []
        for blog in blogs:
            blog_list.append({
                'id': blog[0],
                'title': blog[1],
                'author': blog[2],
                'author_id': blog[3],
                'publish_date': blog[4],
                'url': blog[5],
            })
        
        output_file = os.path.join(DATA_DIR, 'blogs_export.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(blog_list, f, ensure_ascii=False, indent=2)
        
        print(f"已导出 {len(blog_list)} 篇博客到: {output_file}")


def cmd_member(args):
    """指定成员检索命令"""
    print("【模式】指定成员检索（模式2）")
    print(f"【成员】{args.name}")
    print(f"【页数】{args.pages}")
    
    from config import ensure_dirs
    ensure_dirs()
    
    with N46Scraper() as scraper:
        # 第一步：检索成员博客
        print("\n>>> 第一步：检索成员博客")
        total = scraper.crawl_by_member(
            member_name=args.name,
            max_pages=args.pages
        )
        
        if total > 0:
            # 第二步：下载图片
            print(f"\n>>> 第二步：下载 {args.name} 的图片")
            asyncio.run(scraper.download_images_by_member(args.name))
        else:
            print(f"\n未找到 {args.name} 的博客")
    
    print("\n成员检索完成！")


def main():
    """主函数"""
    print_banner()
    
    parser = argparse.ArgumentParser(
        description='乃木坂46博客图片爬虫',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py crawl --pages 5              # 模式1：总检索，爬取前5页
  python main.py download                     # 模式1：下载所有图片
  python main.py full --pages 10              # 模式1：完整流程
  python main.py stats                        # 查看统计
  python main.py member --name "池田 瑛紗"      # 模式2：指定成员检索（默认3页）
  python main.py member --name "小川 彩" --pages 5  # 模式2：指定5页
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # crawl 命令
    crawl_parser = subparsers.add_parser('crawl', help='爬取博客列表')
    crawl_parser.add_argument('--pages', type=int, help='限制爬取页数')

    # download 命令
    download_parser = subparsers.add_parser('download', help='下载图片')

    # stats 命令
    stats_parser = subparsers.add_parser('stats', help='显示统计信息')

    # full 命令
    full_parser = subparsers.add_parser('full', help='完整流程（爬取+下载）')
    full_parser.add_argument('--pages', type=int, help='限制爬取页数')

    # export 命令
    export_parser = subparsers.add_parser('export', help='导出数据')

    # member 命令（指定成员检索 - 模式2）
    member_parser = subparsers.add_parser('member', help='指定成员检索（模式2）')
    member_parser.add_argument('--name', type=str, required=True, help='成员日文名（如"池田 瑛紗"）')
    member_parser.add_argument('--pages', type=int, default=3, help='限制检索页数（默认3页）')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 执行对应命令
    commands = {
        'crawl': cmd_crawl,
        'download': cmd_download,
        'stats': cmd_stats,
        'full': cmd_full,
        'export': cmd_export,
        'member': cmd_member,
    }
    
    if args.command in commands:
        try:
            commands[args.command](args)
        except KeyboardInterrupt:
            print("\n\n⚠ 用户中断操作")
            sys.exit(0)
        except Exception as e:
            print(f"\n错误: {e}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()