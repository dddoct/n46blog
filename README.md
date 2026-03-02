# 乃木坂46博客图片爬虫

一个用于爬取乃木坂46官方博客图片的Python爬虫工具，支持按成员、日期、博客文章等多种方式分类存储。

## 功能特性

- **智能爬取**: 自动解析博客列表和详情页
- **多维度分类**: 图片按成员、日期、博客ID三种方式存储
- **异步下载**: 使用aiohttp实现高效并发下载
- **数据持久化**: SQLite数据库存储博客和图片元数据
- **断点续传**: 支持中断后继续下载
- **统计功能**: 实时查看爬取和下载进度

## 项目结构

```
n46blog/
├── main.py           # 主程序入口
├── scraper.py        # 爬虫核心模块
├── database.py       # 数据库管理
├── config.py         # 配置文件
├── requirements.txt  # 依赖列表
├── README.md         # 说明文档
└── output/           # 输出目录
    ├── data/         # 数据库和导出文件
    └── images/       # 下载的图片
        ├── by_member/  # 按成员分类
        ├── by_date/    # 按日期分类
        └── by_blog/    # 按博客分类
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 爬取博客列表

```bash
# 爬取所有页面
python main.py crawl

# 只爬取前5页
python main.py crawl --pages 5
```

### 2. 下载图片

```bash
# 下载所有待下载的图片
python main.py download
```

### 3. 完整流程（推荐）

```bash
# 爬取并下载（限制10页）
python main.py full --pages 10
```

### 4. 查看统计

```bash
python main.py stats
```

### 5. 导出数据

```bash
python main.py export
```

## 分类存储说明

下载的图片会同时存储到三个目录：

### 按成员分类
```
output/images/by_member/
├── 秋元真夏/
│   ├── 1_xxx.jpg
│   └── 2_xxx.jpg
├── 齋藤飛鳥/
│   └── ...
```

### 按日期分类
```
output/images/by_date/
├── 2024/
│   ├── 01/
│   │   └── xxx.jpg
│   └── 02/
│       └── xxx.jpg
```

### 按博客分类
```
output/images/by_blog/
├── blog_id_1/
│   ├── 1_xxx.jpg
│   └── 2_xxx.jpg
├── blog_id_2/
│   └── ...
```

## 配置说明

编辑 `config.py` 可修改以下配置：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DOWNLOAD_DELAY` | 请求间隔（秒） | 1 |
| `MAX_RETRIES` | 最大重试次数 | 3 |
| `CONCURRENT_DOWNLOADS` | 并发下载数 | 5 |
| `TIMEOUT` | 请求超时（秒） | 30 |

## 注意事项

1. **遵守robots.txt**: 请遵守网站的爬虫协议
2. **控制频率**: 适当调整 `DOWNLOAD_DELAY` 避免对服务器造成压力
3. **版权问题**: 下载的图片仅供个人学习研究使用
4. **网站结构**: 如果网站改版，可能需要调整解析规则

## 数据库结构

### blogs 表
- `id`: 博客ID
- `title`: 标题
- `author`: 作者（成员名）
- `author_id`: 作者ID
- `publish_date`: 发布日期
- `url`: 博客链接
- `content`: 内容（可选）

### images 表
- `id`: 图片ID
- `blog_id`: 所属博客ID
- `original_url`: 原始URL
- `local_path`: 本地路径
- `filename`: 文件名
- `file_size`: 文件大小
- `width/height`: 尺寸
- `download_status`: 下载状态 (0=待下载, 1=已下载)

## 更新日志

### v1.0.0
- 初始版本发布
- 支持博客列表爬取
- 支持图片异步下载
- 支持多维度分类存储

## License

MIT License - 仅供学习研究使用