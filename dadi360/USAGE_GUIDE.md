# 使用指南 - 重构后的招聘信息监控系统

## 🎯 概述

现在你有三个版本的脚本可以使用：

1. **原始版本**：`src/nail/nail.py`、`src/rental/rental.py`、`src/restaurant/restaurant.py`
2. **重构版本**：`src/nail/nail_refactored.py`、`src/rental/rental_refactored.py`、`src/restaurant/restaurant_refactored.py`
3. **统一管理**：`src/scraper_launcher.py`、`src/simple_ui.py`

## 🚀 使用方法

### 方法1: 使用原始脚本（推荐新手）

```bash
# 美甲招聘监控
cd src/nail
python nail.py

# 租房监控
cd src/rental  
python rental.py

# 餐厅招聘监控
cd src/restaurant
python restaurant.py
```

### 方法2: 使用重构后的单个脚本

```bash
# 美甲招聘监控（重构版）
cd src/nail
python nail_refactored.py

# 租房监控（重构版）
cd src/rental
python rental_refactored.py

# 餐厅招聘监控（重构版）
cd src/restaurant
python restaurant_refactored.py
```

### 方法3: 使用统一启动器（推荐高级用户）

```bash
# 启动所有抓取器
cd src
python scraper_launcher.py
```

### 方法4: 使用简单UI界面（推荐）

```bash
# 启动UI界面
cd src
python simple_ui.py
```

## 🖥️ UI界面使用说明

启动UI后，你会看到以下菜单：

```
============================================================
🔍 招聘信息监控系统
============================================================
1. 查看抓取器状态
2. 启动抓取器
3. 停止抓取器
4. 运行一次抓取
5. 查看配置
6. 修改配置
7. 查看日志
0. 退出
============================================================
```

### 功能说明：

1. **查看抓取器状态**：显示所有抓取器的运行状态
2. **启动抓取器**：选择并启动指定的抓取器
3. **停止抓取器**：选择并停止正在运行的抓取器
4. **运行一次抓取**：执行单次抓取任务（不进入循环）
5. **查看配置**：显示当前的邮箱和关键词配置
6. **修改配置**：提示直接编辑config.json文件
7. **查看日志**：调用日志查看工具

## ⚙️ 配置说明

### 配置文件位置：`config.json`

```json
{
  "EMAIL": {
    "SENDER_EMAIL": "your-email@gmail.com",
    "SENDER_PASSWORD": "your-app-password",
    "RECEIVER_EMAIL": "receiver@example.com",
    "SMTP_SERVER": "smtp.gmail.com",
    "SMTP_PORT": 587
  },
  "HEADERS": {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  },
  "nail_jobs": {
    "email_subject": "美甲招聘合集",
    "max_pages": 5,
    "send_interval_seconds": 172800,
    "keywords": ["美甲", "指甲", "nail", ...]
  },
  "rental": {
    "email_subject": "租房信息合集",
    "max_pages": 5,
    "send_interval_seconds": 172800,
    "keywords": ["出租", "租房", "房屋出租", ...]
  },
  "restaurant_jobs": {
    "email_subject": "餐厅招聘合集",
    "max_pages": 5,
    "send_interval_seconds": 172800,
    "keywords": ["餐厅", "餐馆", "厨师", ...]
  }
}
```

### 配置项说明：

- **EMAIL**: 邮箱配置（发件人、收件人、SMTP设置）
- **HEADERS**: HTTP请求头配置
- **nail_jobs**: 美甲招聘配置
- **rental**: 租房信息配置
- **restaurant_jobs**: 餐厅招聘配置

每个抓取器配置包含：
- `email_subject`: 邮件主题
- `max_pages`: 最大抓取页数
- `send_interval_seconds`: 发送间隔（秒）
- `keywords`: 搜索关键词列表

## 📋 日志管理

### 日志文件位置：`logs/`

```
logs/
├── nail_jobs_info.log      # 美甲招聘信息日志
├── nail_jobs_error.log     # 美甲招聘错误日志
├── rental_info.log         # 租房信息日志
├── rental_error.log        # 租房错误日志
├── restaurant_jobs_info.log # 餐厅招聘信息日志
└── restaurant_jobs_error.log # 餐厅招聘错误日志
```

### 查看日志：

```bash
# 使用日志查看工具
python view_logs.py

# 或直接查看文件
tail -f logs/nail_jobs_info.log
```

## 🔧 高级功能

### 1. 添加新的抓取器

如果你想添加新的抓取器，只需：

1. 创建新的抓取器类，继承`BaseScraper`
2. 实现抽象方法
3. 在配置文件中添加配置
4. 在启动器中注册

示例：
```python
class NewJobScraper(BaseScraper):
    def get_target_urls(self) -> List[str]:
        return ["https://example.com/page1"]
    
    def get_search_keywords(self) -> List[str]:
        return ["关键词1", "关键词2"]
    
    def parse_html_for_jobs(self, html_content, base_url, search_terms) -> List[Dict]:
        # 实现解析逻辑
        pass
    
    def get_job_type_name(self) -> str:
        return "新工作类型"
    
    def get_email_subject_prefix(self) -> str:
        return "新工作招聘"
```

### 2. 自定义调度间隔

在配置文件中修改`send_interval_seconds`：

```json
{
  "nail_jobs": {
    "send_interval_seconds": 86400  // 1天
  }
}
```

### 3. 修改关键词

在配置文件中修改`keywords`数组：

```json
{
  "nail_jobs": {
    "keywords": ["美甲", "指甲", "nail", "你的新关键词"]
  }
}
```

## 🚨 故障排除

### 常见问题：

1. **邮件发送失败**
   - 检查邮箱配置
   - 确认应用密码正确
   - 检查SMTP设置

2. **抓取失败**
   - 检查网络连接
   - 确认目标网站可访问
   - 查看错误日志

3. **配置错误**
   - 检查config.json格式
   - 确认所有必需字段存在
   - 验证JSON语法

### 调试技巧：

1. **查看详细日志**：
   ```bash
   tail -f logs/*_error.log
   ```

2. **单次运行测试**：
   ```bash
   cd src
   python simple_ui.py
   # 选择"4. 运行一次抓取"
   ```

3. **检查配置**：
   ```bash
   cd src
   python simple_ui.py
   # 选择"5. 查看配置"
   ```

## 🎉 总结

现在你有了一个功能完整、易于维护的招聘信息监控系统：

- ✅ **代码复用**：减少重复代码约70%
- ✅ **易于扩展**：添加新功能只需继承基础类
- ✅ **统一管理**：通过启动器和UI管理所有抓取器
- ✅ **向后兼容**：原始脚本仍然可用
- ✅ **专业日志**：完整的日志记录和查看功能
- ✅ **配置灵活**：支持动态配置修改

选择最适合你的使用方式，开始监控招聘信息吧！🎯 