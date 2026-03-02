# 紫团博客图片提取

基于 Selenium 的紫团官方博客图片爬取工具，支持真正的分页爬取和多维度分类存储。

## 功能特性

- **双模式检索**
  - 模式1（总检索）：使用 Selenium 遍历总博客页面，支持真正的分页
  - 模式2（成员检索）：针对特定成员的个人博客页面爬取
- **智能爬取**: 自动解析博客列表和详情页，提取所有图片
- **多维度分类**: 图片按成员、日期、博客ID三种方式存储
- **异步下载**: 使用 aiohttp 实现高效并发下载
- **数据持久化**: SQLite 数据库存储博客和图片元数据
- **断点续传**: 支持中断后继续下载

## 项目结构

```
n46blog/
├── main.py              # 主程序入口
├── scraper.py           # 爬虫核心模块（含 Selenium）
├── database.py          # 数据库管理
├── config.py            # 配置文件
├── members.py           # 成员名字映射表
├── requirements.txt     # 依赖列表
├── README.md            # 说明文档
├── 功能说明.md          # 功能详细说明
├── 爬取逻辑说明.md      # 技术实现说明
├── output1/             # 模式1输出目录
│   ├── data/            # 数据库
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

依赖包括：
- requests/aiohttp: HTTP 请求
- BeautifulSoup: HTML 解析
- **Selenium**: 浏览器自动化（用于 mode1 分页）
- webdriver-manager: 自动管理 ChromeDriver

## 使用方法

### 模式1：总检索

使用 Selenium 浏览器访问总博客页面，支持真正的分页爬取。

```bash
# 完整流程（爬取+下载）- 爬取1页
python main.py full

# 完整流程 - 爬取2页
python main.py full --pages 2

# 完整流程 - 爬取5页
python main.py full --pages 5
```

**说明**：
- 每页约 30-40 篇博客（根据网站实际显示）
- 使用 Chrome 浏览器无头模式
- 第一次运行会自动下载 ChromeDriver

### 模式2：指定成员检索

针对特定成员的个人博客页面进行爬取。

```bash
# 指定成员检索（默认3页）
python main.py member --name "池田 瑛紗"

# 指定成员检索（指定5页）
python main.py member --name "小川 彩" --pages 5
```

### 其他命令

```bash
# 仅爬取博客列表（不下载）
python main.py crawl --pages 3

# 仅下载图片（基于已爬取的记录）
python main.py download

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
└── 池田 瑛紗/
    ├── 20241231/
    │   ├── IkedaTeresa_1.png
    │   └── IkedaTeresa_2.jpg
    └── 20250101/
        ├── IkedaTeresa_1.jpg
        └── IkedaTeresa_2.png
```

## 技术说明

### 为什么使用 Selenium？

紫团官网的总博客页面 (`/s/n46/diary/MEMBER`) 使用 JavaScript 动态加载内容：
- 直接请求 HTML 返回空页面（没有博客数据）
- 数据通过 JS 调用 API 动态渲染
- API 本身不支持分页参数（始终返回最新100篇）

**解决方案**：使用 Selenium 浏览器访问页面，等待 JS 渲染完成后解析，实现真正的分页爬取。

### 日期获取逻辑

博客列表页面不显示日期，日期只在博客详情页才有。因此：
1. 先从列表页获取博客基本信息（标题、作者、URL）
2. 访问每篇博客详情页提取准确的发布日期
3. 使用详情页的日期更新数据库记录

### 成员个人页面

成员个人页面 (`/s/n46/diary/MEMBER/list?ct=xxx`) 不使用 JS 动态加载，可以直接用 requests 爬取。

## 注意事项

1. **首次运行**：会自动下载 ChromeDriver，需要几秒钟时间
2. **网络问题**：如果爬取失败，可能是网络连接问题，请重试
3. **磁盘空间**：图片较多，请确保有足够的磁盘空间
4. **遵守规则**：请合理设置爬取间隔，不要对服务器造成过大压力
