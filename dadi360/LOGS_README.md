# 日志系统说明

## 概述
监控脚本现在使用分离的日志系统，将信息日志和错误日志分别存储在不同的文件中，便于管理和查看。所有日志文件都保存在项目根目录的 `logs/` 文件夹中。

## 日志文件结构

### 项目根目录结构
```
dadi360/
├── logs/                          # 日志文件夹 (项目根目录)
│   ├── nail_jobs_info.log        # 美甲招聘信息日志
│   ├── nail_jobs_error.log       # 美甲招聘错误日志
│   ├── rental_info.log           # 租房监控信息日志
│   └── rental_error.log          # 租房监控错误日志
├── src/
│   ├── nail/
│   │   └── nail.py
│   └── rental/
│       └── rental.py
├── config.json
├── view_logs.py                   # 日志查看工具
└── LOGS_README.md                # 本文档
```

### 美甲招聘监控 (`src/nail/nail.py`)
```
logs/
├── nail_jobs_info.log    # 信息日志 (INFO, SUCCESS, WARNING)
└── nail_jobs_error.log   # 错误日志 (ERROR, CRITICAL)
```

### 租房监控 (`src/rental/rental.py`)
```
logs/
├── rental_info.log       # 信息日志 (INFO, SUCCESS, WARNING)
└── rental_error.log      # 错误日志 (ERROR, CRITICAL)
```

## 日志级别说明

### 信息日志 (`*_info.log`)
- **INFO**: 一般运行信息，如开始任务、找到匹配内容等
- **SUCCESS**: 成功操作，如邮件发送成功
- **WARNING**: 警告信息，如获取详情失败、日期解析失败等

### 错误日志 (`*_error.log`)
- **ERROR**: 错误信息，如网络请求失败、邮件发送失败等
- **CRITICAL**: 严重错误，如程序崩溃等

## 日志配置

### 信息日志配置
- 文件大小限制: 10 MB
- 保留时间: 30 天
- 自动轮转: 超过大小限制时自动创建新文件

### 错误日志配置
- 文件大小限制: 5 MB
- 保留时间: 60 天
- 自动轮转: 超过大小限制时自动创建新文件

## 查看日志

### 方法1: 使用日志查看工具
```bash
python3 view_logs.py
```

### 方法2: 直接查看文件
```bash
# 查看美甲招聘信息日志
tail -f logs/nail_jobs_info.log

# 查看美甲招聘错误日志
tail -f logs/nail_jobs_error.log

# 查看租房信息日志
tail -f logs/rental_info.log

# 查看租房错误日志
tail -f logs/rental_error.log
```

### 方法3: 查看所有日志
```bash
# 查看所有信息日志
cat logs/*_info.log

# 查看所有错误日志
cat logs/*_error.log
```

## 日志格式

所有日志都使用统一的格式：
```
YYYY-MM-DD HH:mm:ss | LEVEL | MESSAGE
```

示例：
```
2025-01-15 14:30:25 | INFO | 美甲招聘监控任务开始: 2025-01-15 14:30:25
2025-01-15 14:30:26 | INFO | 正在请求: https://c.dadi360.com/c/forums/show/56.page
2025-01-15 14:30:28 | SUCCESS | 邮件已发送到 aiyouaiyou98@gmail.com
2025-01-15 14:30:29 | ERROR | 请求 https://example.com 失败: Connection timeout
```

## 控制台输出

脚本运行时，控制台会显示：
- 彩色格式的日志信息
- 实时运行状态
- 错误和警告信息

## 日志管理

### 自动清理
- 信息日志超过30天自动删除
- 错误日志超过60天自动删除
- 文件大小超过限制时自动轮转

### 手动清理
```bash
# 删除所有日志文件
rm -rf logs/*.log

# 删除特定脚本的日志
rm logs/nail_jobs_*.log
rm logs/rental_*.log
```

## 故障排除

### 常见问题

1. **日志文件不存在**
   - 确保脚本已经运行过
   - 检查 `logs/` 目录是否存在

2. **日志文件过大**
   - 检查是否有大量错误
   - 考虑调整日志级别或清理旧日志

3. **日志内容混乱**
   - 检查文件编码是否为 UTF-8
   - 确保没有多个进程同时写入

### 调试模式

如果需要更详细的日志，可以临时修改日志级别：
```python
# 在脚本中修改
logger.add("logs/debug.log", level="DEBUG")
```

## 最佳实践

1. **定期检查错误日志**：及时发现和解决问题
2. **监控日志文件大小**：避免磁盘空间不足
3. **备份重要日志**：在清理前备份关键信息
4. **使用日志查看工具**：便于快速查看最新状态 