"""
乃木坂46博客爬虫核心模块 - API版本
"""

import re
import time
import json
import asyncio
import aiohttp
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

from config import (
    BASE_URL, IMAGE_BASE_URL, HEADERS, DOWNLOAD_DELAY,
    MAX_RETRIES, TIMEOUT, CONCURRENT_DOWNLOADS,
    BY_MEMBER_DIR, BY_DATE_DIR, BY_BLOG_DIR,
    IMAGE_EXTENSIONS
)
from database import Database
from members import get_english_name

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class N46Scraper:
    """乃木坂46博客爬虫类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.db = Database()
        self.semaphore = asyncio.Semaphore(CONCURRENT_DOWNLOADS)
        self.api_base = "https://www.nogizaka46.com/s/n46/api"
    
    def fetch_api(self, endpoint, params=None, retries=0):
        """获取API数据（处理JSONP格式）"""
        url = f"{self.api_base}/{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            # 处理JSONP格式: res({...});
            text = response.text
            if text.startswith('res('):
                # 找到对应的结束位置
                json_str = text[4:]  # 去掉 res(
                if json_str.endswith(');'):
                    json_str = json_str[:-2]  # 去掉 );
                elif json_str.endswith(')'):
                    json_str = json_str[:-1]  # 去掉 )
                data = json.loads(json_str)
            else:
                data = response.json()
            
            time.sleep(DOWNLOAD_DELAY)
            return data
        except Exception as e:
            if retries < MAX_RETRIES:
                time.sleep(DOWNLOAD_DELAY * 2)
                return self.fetch_api(endpoint, params, retries + 1)
            print(f"获取API失败: {url}, 错误: {e}")
            return None
    
    def fetch_page(self, url, retries=0):
        """获取页面内容（用于详情页）"""
        try:
            response = self.session.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            response.encoding = 'utf-8'
            time.sleep(DOWNLOAD_DELAY)
            return response.text
        except Exception as e:
            if retries < MAX_RETRIES:
                time.sleep(DOWNLOAD_DELAY * 2)
                return self.fetch_page(url, retries + 1)
            print(f"获取页面失败: {url}, 错误: {e}")
            return None
    
    def parse_blog_list_api(self, data):
        """从API响应中解析博客列表"""
        blogs = []
        
        if not data or 'data' not in data:
            print(f"API响应格式错误: {data.keys() if data else 'None'}")
            return blogs
        
        for item in data['data']:
            try:
                blog = self._extract_blog_info_api(item)
                if blog:
                    blogs.append(blog)
            except Exception as e:
                print(f"解析博客项失败: {e}")
                continue
        
        return blogs
    
    def _extract_blog_info_api(self, item):
        """从API数据中提取博客信息"""
        blog = {}
        
        # 博客ID
        blog['id'] = item.get('code', '')
        
        # 标题
        blog['title'] = item.get('title', '')
        
        # 作者信息
        blog['author'] = item.get('name', '')
        blog['author_id'] = item.get('arti_code', '')
        
        # 日期
        blog['publish_date'] = item.get('date', '')
        
        # 链接 - 构建详情页URL
        blog['url'] = f"https://www.nogizaka46.com/s/n46/diary/detail/{blog['id']}"
        
        # 内容（HTML格式）
        blog['content'] = item.get('text', '')
        
        return blog if blog['id'] else None
    
    def parse_blog_detail(self, html, blog_id):
        """解析博客详情页面，提取图片"""
        soup = BeautifulSoup(html, 'lxml')
        images = []
        
        # 查找所有图片
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src') or img.get('data-src') or img.get('data-original')
            if not src:
                continue
            
            # 过滤非内容图片（如头像、图标等）
            if self._is_content_image(img):
                img_url = urljoin(IMAGE_BASE_URL, src)
                images.append({
                    'blog_id': blog_id,
                    'original_url': img_url,
                    'alt': img.get('alt', ''),
                })
        
        return images
    
    def _is_content_image(self, img_tag):
        """判断是否为内容图片（非装饰性图片）"""
        # 排除小图标
        width = img_tag.get('width')
        height = img_tag.get('height')
        
        if width and height:
            try:
                if int(width) < 100 or int(height) < 100:
                    return False
            except:
                pass
        
        # 排除特定class
        img_class = ' '.join(img_tag.get('class', []))
        exclude_patterns = ['icon', 'avatar', 'logo', 'banner', 'emoji']
        for pattern in exclude_patterns:
            if pattern in img_class.lower():
                return False
        
        return True
    
    def _create_selenium_driver(self):
        """创建Selenium浏览器驱动"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 无头模式
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    
    def _parse_total_blog_page(self, driver, page_num):
        """使用Selenium解析总博客页面
        
        Args:
            driver: Selenium WebDriver
            page_num: 页码（从1开始）
            
        Returns:
            list: 博客列表
        """
        url = f"https://www.nogizaka46.com/s/n46/diary/MEMBER?ima=5900&page={page_num}"
        print(f"  正在加载页面...", end=" ")
        
        try:
            driver.get(url)
            
            # 等待页面加载完成（等待博客列表出现）
            wait = WebDriverWait(driver, 10)
            # 等待包含博客链接的元素出现
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/diary/detail/']")))
            
            # 再等待一下确保JavaScript渲染完成
            time.sleep(2)
            
            # 获取页面源码
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找博客链接
            blog_links = soup.find_all('a', href=re.compile(r'/s/n46/diary/detail/\d+'))
            print(f"找到 {len(blog_links)} 个博客链接")
            
            blogs = []
            for link in blog_links:
                href = link.get('href', '')
                blog_id_match = re.search(r'/detail/(\d+)', href)
                if not blog_id_match:
                    continue
                
                blog_id = blog_id_match.group(1)
                
                # 获取标题
                title_elem = link.find(class_=re.compile('title|tit', re.I)) or link
                title = title_elem.get_text().strip()
                
                # 获取作者
                author_elem = link.find(class_=re.compile('name|author|member', re.I))
                author = author_elem.get_text().strip() if author_elem else 'unknown'
                
                # 获取日期
                date_elem = link.find(class_=re.compile('date|time', re.I))
                date_str = date_elem.get_text().strip() if date_elem else ''
                
                # 解析日期 - 支持多种格式
                publish_date = 'unknown'
                if date_str:
                    # 清理日期字符串
                    date_clean = date_str.split()[0] if ' ' in date_str else date_str
                    
                    for fmt in ['%Y.%m.%d', '%Y/%m/%d', '%Y-%m-%d']:
                        try:
                            dt = datetime.strptime(date_clean, fmt)
                            publish_date = dt.strftime('%Y/%m/%d %H:%M:%S')
                            break
                        except:
                            continue
                
                if title and blog_id:
                    blogs.append({
                        'id': blog_id,
                        'title': title,
                        'author': author,
                        'publish_date': publish_date,
                        'url': f"https://www.nogizaka46.com/s/n46/diary/detail/{blog_id}"
                    })
            
            return blogs
            
        except Exception as e:
            print(f"错误: {e}")
            return []
    
    def crawl_blog_list(self, start_page=1, max_pages=None):
        """爬取博客列表 - 使用Selenium实现真正的分页
        
        通过Selenium浏览器访问总博客页面，支持真正的分页功能。
        
        Args:
            start_page: 起始页码（从1开始）
            max_pages: 最大爬取页数（默认None表示无限制）
        """
        print(f"开始爬取博客列表...")
        print(f"起始页: {start_page}, 最大页数: {max_pages if max_pages else '无限制'}")
        print("="*60)
        
        # 创建Selenium驱动
        print("\n正在启动浏览器...")
        driver = None
        try:
            driver = self._create_selenium_driver()
            print("浏览器启动成功")
        except Exception as e:
            print(f"浏览器启动失败: {e}")
            print("请确保已安装Chrome浏览器")
            return 0
        
        total_blogs = 0
        processed_blogs = set()  # 用于去重
        current_page = start_page
        
        try:
            while max_pages is None or (current_page - start_page) < max_pages:
                print(f"\n{'='*60}")
                print(f"正在爬取第 {current_page} 页")
                print(f"{'='*60}")
                
                # 解析页面
                blogs = self._parse_total_blog_page(driver, current_page)
                
                if not blogs:
                    print("本页无博客，停止爬取")
                    break
                
                new_blogs = 0
                for blog in blogs:
                    # 去重检查
                    if blog['id'] in processed_blogs:
                        continue
                    processed_blogs.add(blog['id'])
                    
                    total_blogs += 1
                    new_blogs += 1
                    
                    print(f"  [{total_blogs}] {blog['title'][:30]}... - {blog['author']}")
                    
                    # 获取博客详情（包含图片）
                    blog_detail = self._fetch_blog_detail(blog['url'])
                    if blog_detail:
                        blog['content'] = blog_detail.get('content', '')
                        blog['images'] = blog_detail.get('images', [])
                    
                    # 保存博客信息
                    self.db.save_blog(blog)
                    
                    # 保存图片信息
                    for img_url in blog.get('images', []):
                        img_data = {
                            'blog_id': blog['id'],
                            'original_url': img_url,
                            'local_path': None,
                            'download_status': 0
                        }
                        self.db.save_image(img_data)
                
                print(f"\n第 {current_page} 页完成: {new_blogs} 篇新博客")
                
                # 如果这页没有新博客，可能是到了末尾
                if new_blogs == 0:
                    print("没有新博客了，停止爬取")
                    break
                
                current_page += 1
                time.sleep(DOWNLOAD_DELAY * 2)  # Selenium需要更多延迟
                
        finally:
            # 关闭浏览器
            if driver:
                driver.quit()
                print("\n浏览器已关闭")
        
        print(f"\n{'='*60}")
        print(f"博客列表爬取完成！")
        print(f"  共爬取: {current_page - start_page} 页")
        print(f"  共获取: {total_blogs} 篇唯一博客")
        print(f"{'='*60}")
        return total_blogs
        
        print(f"\n{'='*60}")
        print(f"博客列表爬取完成！")
        print(f"  共处理: {len(members)} 名成员")
        print(f"  共获取: {total_blogs} 篇唯一博客")
        print(f"{'='*60}")
        return total_blogs
    
    def _get_all_members(self):
        """获取所有成员列表
        
        Returns:
            list: [(成员名, 成员ID), ...]
        """
        members = []
        
        try:
            # 使用API获取成员列表
            data = self.fetch_api("list/member")
            if data and 'data' in data:
                for item in data['data']:
                    name = item.get('name', '')
                    # API使用'code'字段作为成员ID，不是'id'
                    member_id = item.get('code', '')
                    # 过滤掉团体条目（如"乃木坂46"）和毕业成员
                    # 只保留有生日信息的（是真实成员）
                    birthday = item.get('birthday', '')
                    graduation = item.get('graduation', '')
                    if name and member_id and birthday and graduation != 'YES':
                        members.append((name, member_id))
        except Exception as e:
            print(f"获取成员列表失败: {e}")
        
        return members
    
    def _extract_images_from_content(self, content_html, blog_id):
        """从博客内容HTML中提取图片"""
        images = []
        
        if not content_html:
            return images
        
        soup = BeautifulSoup(content_html, 'lxml')
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src')
            if src:
                # 处理相对路径
                if src.startswith('/'):
                    img_url = f"https://www.nogizaka46.com{src}"
                elif src.startswith('http'):
                    img_url = src
                else:
                    img_url = f"https://www.nogizaka46.com/{src}"
                
                images.append({
                    'blog_id': blog_id,
                    'original_url': img_url,
                    'alt': img.get('alt', ''),
                })
        
        return images
    
    async def download_images(self):
        """异步下载所有待下载的图片"""
        pending_images = self.db.get_pending_images(limit=1000)
        
        if not pending_images:
            print("没有待下载的图片")
            return
        
        print(f"\n开始下载 {len(pending_images)} 张图片...")
        print("="*60)
        
        # 按博客ID分组图片，用于计算序号
        blog_images = {}
        for img in pending_images:
            blog_id = img[1]
            if blog_id not in blog_images:
                blog_images[blog_id] = []
            blog_images[blog_id].append(img)
        
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            tasks = []
            for blog_id, images in blog_images.items():
                for idx, img in enumerate(images, 1):
                    task = self._download_single_image(session, img, idx, len(images))
                    tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success = sum(1 for r in results if r is True)
            failed = len(results) - success
            
            print(f"\n{'='*60}")
            print(f"下载完成: 成功 {success} 张, 失败 {failed} 张")
            print(f"{'='*60}")
    
    async def _download_single_image(self, session, img_data, img_index, total_images):
        """下载单张图片
        
        Args:
            session: aiohttp session
            img_data: 图片数据 (id, blog_id, original_url, ...)
            img_index: 该博客中的第几张图片（从1开始）
            total_images: 该博客总共有多少张图片
        """
        async with self.semaphore:
            img_id = img_data[0]
            blog_id = img_data[1]
            original_url = img_data[2]
            
            try:
                # 获取博客信息用于分类
                self.db.cursor.execute(
                    'SELECT author, publish_date FROM blogs WHERE id = ?', (blog_id,)
                )
                blog_info = self.db.cursor.fetchone()
                author = blog_info[0] if blog_info else 'unknown'
                date = blog_info[1] if blog_info else 'unknown'
                
                # 获取英文名
                english_name = get_english_name(author)
                
                # 解析日期 - API格式: 2026/03/01 21:44:02
                # 格式化为: 20260301
                date_str = 'unknown'
                yearmonth = 'unknown'
                if date and date != 'unknown':
                    try:
                        for fmt in ['%Y/%m/%d %H:%M:%S', '%Y.%m.%d', '%Y-%m-%d']:
                            try:
                                dt = datetime.strptime(date, fmt)
                                date_str = dt.strftime('%Y%m%d')  # 格式: 20260301
                                yearmonth = dt.strftime('%Y%m')    # 格式: 202603
                                break
                            except:
                                continue
                    except:
                        pass
                
                # 获取文件扩展名
                ext = self._get_extension(original_url)
                
                # 任务1: by_member - 按成员分子目录，文件名: 英文成员名_日期_序号.jpg
                # 例如: by_member/小川 彩/OgawaAya_20260301_1.jpg
                member_filename = f"{english_name}_{date_str}_{img_index}{ext}"
                member_dir = Path(BY_MEMBER_DIR) / author  # 使用日文原名作为目录名
                
                # 任务2: by_date - 按年月/日期分子目录，文件名: 英文成员名_序号.jpg
                # 例如: by_date/202601/20260102/OgawaAya_1.jpg
                date_filename = f"{english_name}_{img_index}{ext}"
                date_dir = Path(BY_DATE_DIR) / yearmonth / date_str  # 202601/20260102
                
                # 任务3: by_blog - 保持原有格式
                blog_filename = self._generate_filename(original_url, img_id)
                blog_dir = Path(BY_BLOG_DIR) / blog_id
                
                paths = {
                    'by_member': member_dir / member_filename,
                    'by_date': date_dir / date_filename,
                    'by_blog': blog_dir / blog_filename,
                }
                
                # 下载图片
                async with session.get(original_url, timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # 保存到所有分类目录
                        saved_paths = []
                        for category, filepath in paths.items():
                            filepath.parent.mkdir(parents=True, exist_ok=True)
                            with open(filepath, 'wb') as f:
                                f.write(content)
                            saved_paths.append(str(filepath))
                        
                        # 更新数据库状态
                        self.db.update_image_status(img_id, 1, saved_paths[0])
                        return True
                    else:
                        print(f"  ✗ 下载失败: {original_url} (状态码: {response.status})")
                        return False
                        
            except Exception as e:
                print(f"  ✗ 下载图片出错: {original_url[:60]}... 错误: {e}")
                return False
    
    def _get_extension(self, url):
        """从URL获取文件扩展名"""
        parsed = urlparse(url)
        original_name = Path(parsed.path).name
        
        if '.' in original_name:
            ext = Path(original_name).suffix.lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
                return ext
        
        return '.jpg'  # 默认扩展名
    
    def _generate_filename(self, url, img_id):
        """生成文件名（用于by_blog）"""
        parsed = urlparse(url)
        original_name = Path(parsed.path).name
        
        if not original_name or '.' not in original_name:
            ext = '.jpg'
            return f"{img_id}{ext}"
        
        name = self._sanitize_filename(original_name)
        return f"{img_id}_{name}"
    
    def _sanitize_filename(self, filename):
        """清理文件名中的非法字符"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip() or 'unknown'
    
    def crawl_by_member(self, member_name, max_pages=3):
        """指定成员检索模式 - 使用成员个人blog网页
        
        Args:
            member_name: 成员日文名（如"池田 瑛紗"）
            max_pages: 最大爬取页数（默认3页，每页10篇博客）
            
        Returns:
            爬取的博客数量
        """
        # 首先获取成员ID
        member_id = self._get_member_id(member_name)
        if not member_id:
            print(f"未找到成员: {member_name}")
            print("请确保成员名字正确，或使用模式1先爬取成员列表")
            return 0
        
        print(f"开始检索成员: {member_name} (ID: {member_id})")
        print(f"页数限制: {max_pages} (每页约10篇博客)")
        print("="*60)
        
        page = 0  # 从0开始，第1页对应page=0
        total_blogs = 0
        
        while True:
            print(f"\n正在获取第 {page + 1} 页...")
            
            # 使用成员个人blog界面的网页
            # 注意：第1页是page=0，第2页是page=1
            url = f"https://www.nogizaka46.com/s/n46/diary/MEMBER/list"
            params = {"ct": member_id, "page": page}
            
            try:
                response = self.session.get(url, params=params, timeout=TIMEOUT)
                response.raise_for_status()
                response.encoding = 'utf-8'
                html = response.text
                time.sleep(DOWNLOAD_DELAY)
            except Exception as e:
                print(f"获取页面失败: {e}")
                break
            
            # 解析博客列表
            blogs = self._parse_member_blog_list(html, member_name)
            
            if not blogs:
                print("没有更多博客了")
                break
            
            print(f"获取到 {len(blogs)} 篇博客")
            
            for blog in blogs:
                total_blogs += 1
                
                # 获取博客详情（包含图片）
                blog_detail = self._fetch_blog_detail(blog['url'])
                if blog_detail:
                    blog['content'] = blog_detail.get('content', '')
                    blog['images'] = blog_detail.get('images', [])
                
                # 保存博客信息
                self.db.save_blog(blog)
                
                # 保存图片信息
                for img_url in blog.get('images', []):
                    img_data = {
                        'blog_id': blog['id'],
                        'original_url': img_url,
                        'local_path': None,
                        'download_status': 0
                    }
                    self.db.save_image(img_data)
                
                # 过滤emoji字符避免编码错误
                title = blog['title'][:30].encode('gbk', errors='ignore').decode('gbk')
                print(f"  + [{total_blogs}] {title}... - 日期: {blog['publish_date'][:10]} - 图片: {len(blog.get('images', []))}张")
            
            print(f"  进度: 第{page + 1}页，本页{len(blogs)}篇")
            
            page += 1
            if page >= max_pages:
                print(f"\n已达到最大页数限制 ({max_pages})")
                break
        
        print(f"\n{'='*60}")
        print(f"成员检索完成！")
        print(f"  共获取: {total_blogs} 篇博客")
        print(f"{'='*60}")
        return total_blogs
    
    def _parse_member_blog_list(self, html, member_name):
        """解析成员博客列表页面
        
        Args:
            html: 网页HTML
            member_name: 成员日文名
            
        Returns:
            博客列表
        """
        from bs4 import BeautifulSoup
        import re
        
        soup = BeautifulSoup(html, 'html.parser')
        blogs = []
        
        # 查找博客链接
        links = soup.find_all('a', href=re.compile(r'/s/n46/diary/detail/\d+'))
        
        for link in links:
            href = link.get('href', '')
            if not href:
                continue
            
            # 提取博客ID
            blog_id_match = re.search(r'/s/n46/diary/detail/(\d+)', href)
            if not blog_id_match:
                continue
            blog_id = blog_id_match.group(1)
            
            # 获取链接文本（包含标题和日期）
            link_text = link.get_text().strip()
            
            # 解析标题和日期
            # 格式通常是: 标题\n\n日期时间
            lines = [line.strip() for line in link_text.split('\n') if line.strip()]
            if len(lines) >= 2:
                title = lines[0]
                date_str = lines[-1]
            else:
                title = link_text
                date_str = 'unknown'
            
            # 构建完整URL
            full_url = f"https://www.nogizaka46.com{href.split('?')[0]}"
            
            blog = {
                'id': blog_id,
                'title': title,
                'author': member_name,
                'author_id': None,
                'publish_date': date_str,
                'url': full_url,
                'content': '',
                'images': []
            }
            blogs.append(blog)
        
        return blogs
    
    def _fetch_blog_detail(self, url):
        """获取博客详情
        
        Args:
            url: 博客URL
            
        Returns:
            博客详情字典
        """
        try:
            response = self.session.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            response.encoding = 'utf-8'
            html = response.text
            time.sleep(DOWNLOAD_DELAY)
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找博客内容区域 - 尝试多种可能的选择器
            content_div = None
            selectors = [
                'div.blog-article',
                'article',
                'div[class*="blog"]',
                'div[class*="content"]',
                'div[class*="article"]',
                'main',
                '.main',
                '#main'
            ]
            
            for selector in selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    break
            
            # 如果还是没找到，使用整个body
            if not content_div:
                content_div = soup.body
            
            if not content_div:
                return None
            
            content = str(content_div)
            
            # 提取图片（从整个页面中）
            images = []
            for img in soup.find_all('img'):
                src = img.get('src', '')
                if src:
                    # 过滤掉非博客图片（如logo、图标等）
                    if '/diary/' in src or '/blog/' in src or '/files/' in src:
                        # 转换为完整URL
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = 'https://www.nogizaka46.com' + src
                        if src not in images:
                            images.append(src)
            
            return {
                'content': content,
                'images': images
            }
            
        except Exception as e:
            print(f"获取博客详情失败: {url}, 错误: {e}")
            return None
    
    def _get_member_id(self, member_name):
        """根据成员名字获取成员ID
        
        Args:
            member_name: 成员日文名
            
        Returns:
            成员ID或None
        """
        # 先尝试从数据库获取
        self.db.cursor.execute(
            'SELECT DISTINCT author_id FROM blogs WHERE author LIKE ? LIMIT 1',
            (f'%{member_name}%',)
        )
        result = self.db.cursor.fetchone()
        if result and result[0]:
            return result[0]
        
        # 如果数据库中没有，尝试从API获取成员列表
        try:
            # 获取一页博客来查找成员ID
            params = {"page": 1}
            data = self.fetch_api("list/blog", params)
            if data and data.get('data'):
                for item in data['data']:
                    if member_name in item.get('name', ''):
                        return item.get('arti_code')
        except Exception as e:
            print(f"获取成员ID失败: {e}")
        
        return None
    
    async def download_images_by_member(self, member_name):
        """下载指定成员的图片到output2目录
        
        Args:
            member_name: 成员日文名
        """
        from config import MEMBER_IMAGES_DIR
        from members import get_english_name
        
        # 获取该成员的所有待下载图片
        self.db.cursor.execute('''
            SELECT i.id, i.blog_id, i.original_url, b.author, b.publish_date
            FROM images i
            JOIN blogs b ON i.blog_id = b.id
            WHERE b.author LIKE ? AND i.download_status = 0
        ''', (f'%{member_name}%',))
        
        pending_images = self.db.cursor.fetchall()
        
        if not pending_images:
            print(f"没有待下载的 {member_name} 的图片")
            return
        
        print(f"\n开始下载 {member_name} 的 {len(pending_images)} 张图片...")
        print("="*60)
        
        # 按博客ID分组
        blog_images = {}
        for img in pending_images:
            blog_id = img[1]
            if blog_id not in blog_images:
                blog_images[blog_id] = []
            blog_images[blog_id].append(img)
        
        # 获取英文名
        english_name = get_english_name(member_name)
        
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            tasks = []
            for blog_id, images in blog_images.items():
                for idx, img in enumerate(images, 1):
                    task = self._download_single_image_by_member(
                        session, img, idx, english_name, member_name
                    )
                    tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success = sum(1 for r in results if r is True)
            failed = len(results) - success
            
            print(f"\n{'='*60}")
            print(f"下载完成: 成功 {success} 张, 失败 {failed} 张")
            print(f"{'='*60}")
    
    async def _download_single_image_by_member(self, session, img_data, img_index, 
                                                english_name, member_jp_name):
        """下载单张图片到output2目录
        
        Args:
            session: aiohttp session
            img_data: 图片数据
            img_index: 该博客中的第几张图片
            english_name: 成员英文名
            member_jp_name: 成员日文名
        """
        async with self.semaphore:
            img_id = img_data[0]
            blog_id = img_data[1]
            original_url = img_data[2]
            author = img_data[3]
            date = img_data[4]
            
            try:
                # 解析日期 - 支持多种格式
                date_str = 'unknown'
                if date and date != 'unknown':
                    # 清理日期字符串（去除时间部分）
                    date_clean = date.split()[0] if ' ' in date else date
                    
                    for fmt in ['%Y/%m/%d', '%Y.%m.%d', '%Y-%m-%d', '%Y/%m/%d %H:%M:%S', '%Y.%m.%d %H:%M:%S']:
                        try:
                            dt = datetime.strptime(date_clean, fmt)
                            date_str = dt.strftime('%Y%m%d')
                            break
                        except:
                            continue
                
                # 获取文件扩展名
                ext = self._get_extension(original_url)
                
                # 构建保存路径: output2/images/成员名/日期/英文_序号.jpg
                from config import MEMBER_IMAGES_DIR
                filename = f"{english_name}_{img_index}{ext}"
                save_dir = Path(MEMBER_IMAGES_DIR) / member_jp_name / date_str
                filepath = save_dir / filename
                
                # 下载图片
                async with session.get(original_url, timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # 保存文件
                        filepath.parent.mkdir(parents=True, exist_ok=True)
                        with open(filepath, 'wb') as f:
                            f.write(content)
                        
                        # 更新数据库状态
                        self.db.update_image_status(img_id, 1, str(filepath))
                        return True
                    else:
                        print(f"  ✗ 下载失败: {original_url} (状态码: {response.status})")
                        return False
                        
            except Exception as e:
                print(f"  ✗ 下载图片出错: {original_url[:60]}... 错误: {e}")
                return False
    
    def close(self):
        """关闭资源"""
        self.db.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()