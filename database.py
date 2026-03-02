"""
数据库管理模块 - 存储博客和图片元数据
"""

import sqlite3
import json
from datetime import datetime
from config import DB_PATH, ensure_dirs


class Database:
    def __init__(self):
        ensure_dirs()
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self._init_tables()
    
    def _init_tables(self):
        """初始化数据库表"""
        # 博客表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS blogs (
                id TEXT PRIMARY KEY,
                title TEXT,
                author TEXT,
                author_id TEXT,
                publish_date TEXT,
                url TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 图片表 - 使用blog_id + original_url作为唯一约束
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                blog_id TEXT,
                original_url TEXT,
                local_path TEXT,
                filename TEXT,
                file_size INTEGER,
                width INTEGER,
                height INTEGER,
                download_status INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(blog_id, original_url),
                FOREIGN KEY (blog_id) REFERENCES blogs(id)
            )
        ''')
        
        # 成员表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS members (
                id TEXT PRIMARY KEY,
                name TEXT,
                name_kana TEXT,
                team TEXT,
                generation INTEGER
            )
        ''')
        
        self.conn.commit()
    
    def save_blog(self, blog_data):
        """保存博客信息 - 已存在的会更新"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO blogs (id, title, author, author_id, publish_date, url, content)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            blog_data['id'],
            blog_data.get('title', ''),
            blog_data.get('author', ''),
            blog_data.get('author_id', ''),
            blog_data.get('publish_date', ''),
            blog_data.get('url', ''),
            blog_data.get('content', '')
        ))
        self.conn.commit()
    
    def save_image(self, image_data):
        """保存图片信息 - 如果已存在则跳过"""
        try:
            self.cursor.execute('''
                INSERT INTO images 
                (blog_id, original_url, local_path, filename, file_size, width, height)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                image_data['blog_id'],
                image_data['original_url'],
                image_data.get('local_path', ''),
                image_data.get('filename', ''),
                image_data.get('file_size', 0),
                image_data.get('width', 0),
                image_data.get('height', 0)
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            # 图片已存在，返回已存在的记录ID
            self.cursor.execute('''
                SELECT id FROM images WHERE blog_id = ? AND original_url = ?
            ''', (image_data['blog_id'], image_data['original_url']))
            result = self.cursor.fetchone()
            return result[0] if result else None
    
    def image_exists(self, blog_id, original_url):
        """检查图片是否已存在"""
        self.cursor.execute('''
            SELECT id FROM images WHERE blog_id = ? AND original_url = ?
        ''', (blog_id, original_url))
        return self.cursor.fetchone() is not None
    
    def update_image_status(self, image_id, status, local_path=None):
        """更新图片下载状态"""
        if local_path:
            self.cursor.execute('''
                UPDATE images SET download_status = ?, local_path = ? WHERE id = ?
            ''', (status, local_path, image_id))
        else:
            self.cursor.execute('''
                UPDATE images SET download_status = ? WHERE id = ?
            ''', (status, image_id))
        self.conn.commit()
    
    def get_blogs_by_author(self, author):
        """按作者获取博客"""
        self.cursor.execute('SELECT * FROM blogs WHERE author = ? ORDER BY publish_date DESC', (author,))
        return self.cursor.fetchall()
    
    def get_blogs_by_date(self, start_date, end_date):
        """按日期范围获取博客"""
        self.cursor.execute('''
            SELECT * FROM blogs 
            WHERE publish_date BETWEEN ? AND ? 
            ORDER BY publish_date DESC
        ''', (start_date, end_date))
        return self.cursor.fetchall()
    
    def get_images_by_blog(self, blog_id):
        """获取博客的所有图片"""
        self.cursor.execute('SELECT * FROM images WHERE blog_id = ?', (blog_id,))
        return self.cursor.fetchall()
    
    def get_pending_images(self, limit=100):
        """获取待下载的图片"""
        self.cursor.execute('''
            SELECT * FROM images 
            WHERE download_status = 0 
            LIMIT ?
        ''', (limit,))
        return self.cursor.fetchall()
    
    def get_stats(self):
        """获取统计信息"""
        stats = {}
        
        # 博客总数
        self.cursor.execute('SELECT COUNT(*) FROM blogs')
        stats['total_blogs'] = self.cursor.fetchone()[0]
        
        # 图片总数
        self.cursor.execute('SELECT COUNT(*) FROM images')
        stats['total_images'] = self.cursor.fetchone()[0]
        
        # 已下载图片数
        self.cursor.execute('SELECT COUNT(*) FROM images WHERE download_status = 1')
        stats['downloaded_images'] = self.cursor.fetchone()[0]
        
        # 成员数
        self.cursor.execute('SELECT COUNT(DISTINCT author) FROM blogs')
        stats['total_authors'] = self.cursor.fetchone()[0]
        
        return stats
    
    def clear_all_data(self):
        """清空所有数据（谨慎使用）"""
        self.cursor.execute('DELETE FROM images')
        self.cursor.execute('DELETE FROM blogs')
        self.conn.commit()
        print("已清空所有数据")
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
