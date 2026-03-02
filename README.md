# 紫团博客图片爬虫

一个用于爬取紫团官方博客图片的Python爬虫工具，支持两种检索模式：总检索（模式1）和指定成员检索（模式2）。

## 功能特性

- **双模式检索**：
  - 模式1：总检索 - 爬取所有成员博客，多维度分类存储
  - 模式2：指定成员检索 - 针对特定成员的个人博客页面爬取
- **智能爬取**: 自动解析博客列表和详情页
- **多维度分类**: 图片按成员、日期、博客ID三种方式存储
- **异步下载**: 使用aiohttp实现高效并发下载
- **数据持久化**: SQLite数据库存储博客和图片元数据
- **断点续传**: 支持中断后继续下载
- **统计功能**: 实时查看爬取和下载进度

## 项目结构

```
n46blog/
├── main.py              # 主程序入口
├── scraper.py           # 爬虫核心模块
├── database.py          # 数据库管理
├── config.py            # 配置文件
├── members.py           # 成员名字映射表
├── requirements.txt     # 依赖列表
├── README.md            # 说明文档
├── 功能说明.md          # 功能详细说明
├── 爬取逻辑说明.md      # 技术实现说明
├── output1/             # 模式1输出目录
│   ├── data/            # 数据库和导出文件
│   │   └── n46_blog.db
│   └── images/          # 下载的图片
│       ├── by_member/   # 按成员分类
│       ├── by_date/     # 按日期分类
│       └── by_blog/     # 按博客分类
└── output2/             # 模式2输出目录
    └── images/          # 指定成员的图片
        └── 成员名/
            └── 日期/
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 模式1：总检索

爬取所有成员的博客，存储到 `output1/` 目录。

```bash
# 爬取博客列表（限制5页）
python main.py crawl --pages 5

# 下载图片
python main.py download

# 完整流程（爬取+下载）
python main.py full --pages 10
```

### 模式2：指定成员检索

针对特定成员的个人博客页面进行爬取，存储到 `output2/` 目录。

```bash
# 指定成员检索（默认3页）
python main.py member --name "池田 瑛紗"

# 指定成员检索（指定5页）
python main.py member --name "小川 彩" --pages 5
```

### 其他命令

```bash
# 查看统计
python main.py stats

# 导出数据
python main.py export

# 查看帮助
python main.py --help
```

## 分类存储说明

### 模式1 - 总检索存储结构

#### 按成员分类 (by_member)
```
output1/images/by_member/
├── 池田 瑛紗/
│   ├── IkedaTeresa_20260301_1.jpg
│   └── IkedaTeresa_20260301_2.jpg
├── 小川 彩/
│   └── OgawaAya_20260301_1.jpg
```

#### 按日期分类 (by_date)
```
output1/images/by_date/
├── 202601/
│   ├── 20260101/
│   │   ├── OgawaAya_1.jpg
│   │   └── IkedaTeresa_1.jpg
│   └── 20260102/
│       └── ...
```

#### 按博客分类 (by_blog)
```
output1/images/by_blog/
├── 104302/
│   ├── 1_mobq2EkxC.jpg
│   └── 2_mobdeEYoR.jpg
```

### 模式2 - 指定成员检索存储结构

```
output2/images/
├── 池田 瑛紗/
│   ├── 20241231/
│   │   ├── IkedaTeresa_1.png
│   │   └── IkedaTeresa_2.jpg
│   └── 20250101/
│       ├── IkedaTeresa_1.jpg
│       └── IkedaTeresa_2.png
└── 小川 彩/
    └── 20250301/
        └── OgawaAya_1.jpg
```

## 两种模式对比

| 特性 | 模式1：总检索 | 模式2：指定成员检索 |
|------|--------------|-------------------|
| 命令 | `crawl` / `full` | `member` |
| 输出目录 | `output1/` | `output2/` |
| 爬取范围 | 所有成员 | 指定成员 |
| 适用场景 | 全量备份 | 特定成员追踪 |
| 页数控制 | `--pages` | `--pages`（默认3） |
| API方式 | 通用列表API | 成员个人页面API |

## 成员名字格式

使用成员日文全名（带空格），例如：
- `"池田 瑛紗"`
- `"小川 彩"`
- `"遠藤 さくら"`
- `"賀喜 遥香"`
- `"井上 和"`

## 技术说明

- 基于紫团官方API：`https://www.nogizaka46.com/s/n46/api/list/blog`
- 支持JSONP响应解析
- 使用SQLite数据库进行数据持久化
- 异步下载提高性能

## 详细文档

- [功能说明.md](功能说明.md) - 功能详细说明
- [爬取逻辑说明.md](爬取逻辑说明.md) - 技术实现细节

## 注意事项

1. 请合理使用爬虫，避免频繁请求对服务器造成压力
2. 建议设置适当的页数限制（`--pages`）
3. 模式2需要先通过模式1爬取一次以获取成员ID映射，或直接从API获取
4. 图片仅供个人学习研究使用，请遵守相关法律法规
