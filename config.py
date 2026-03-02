"""
乃木坂46博客爬虫配置文件
"""

import os

# 基础URL
BASE_URL = "https://www.nogizaka46.com/s/n46/diary/MEMBER"
IMAGE_BASE_URL = "https://www.nogizaka46.com"

# 请求配置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,ja;q=0.8,en;q=0.7',
    'Referer': 'https://www.nogizaka46.com/',
}

# 下载配置
DOWNLOAD_DELAY = 1  # 请求间隔(秒)
MAX_RETRIES = 3
TIMEOUT = 30
CONCURRENT_DOWNLOADS = 5

# 存储路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
IMAGES_DIR = os.path.join(OUTPUT_DIR, 'images')
DATA_DIR = os.path.join(OUTPUT_DIR, 'data')

# 分类存储子目录
BY_MEMBER_DIR = os.path.join(IMAGES_DIR, 'by_member')
BY_DATE_DIR = os.path.join(IMAGES_DIR, 'by_date')
BY_BLOG_DIR = os.path.join(IMAGES_DIR, 'by_blog')

# 数据库配置
DB_PATH = os.path.join(DATA_DIR, 'n46_blog.db')

# 支持的图片格式
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']

# 创建目录
def ensure_dirs():
    """确保所有必要的目录都存在"""
    dirs = [OUTPUT_DIR, IMAGES_DIR, DATA_DIR, BY_MEMBER_DIR, BY_DATE_DIR, BY_BLOG_DIR]
    for d in dirs:
        os.makedirs(d, exist_ok=True)