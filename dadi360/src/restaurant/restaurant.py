import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import time
import os
import json
import urllib3
import re
import sys
from loguru import logger
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from scheduler_util import Scheduler

# 配置loguru日志
logger.remove()  # 移除默认处理器

# 获取项目根目录的绝对路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# 信息日志 - 记录所有INFO及以上级别的日志
logger.add(
    os.path.join(LOGS_DIR, "restaurant_jobs_info.log"),
    rotation="10 MB",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    encoding="utf-8",
    filter=lambda record: record["level"].name in ["INFO", "SUCCESS", "WARNING"]
)

# 错误日志 - 只记录ERROR及以上级别的日志
logger.add(
    os.path.join(LOGS_DIR, "restaurant_jobs_error.log"),
    rotation="5 MB",
    retention="60 days",
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    encoding="utf-8",
    filter=lambda record: record["level"].name in ["ERROR", "CRITICAL"]
)

# 控制台输出 - 显示所有INFO及以上级别的日志
logger.add(
    sys.stdout,
    level="INFO",
    format="{time:HH:mm:ss} | {level} | {message}",
    colorize=True
)

# 确保日志目录存在
os.makedirs(LOGS_DIR, exist_ok=True)

# 抑制SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 配置信息从 config.json 加载 ---
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../../config.json')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

# --- 辅助函数：持久化已发送ID ---
def load_sent_ids(file_path):
    """从文件中加载已发送的招聘信息ID集合。"""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"加载已发送ID文件失败 {file_path}: {e}. 初始化为空集合。")
            return set()
    return set()

def save_sent_ids(file_path, ids_set):
    """将已发送的招聘信息ID集合保存到文件。"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(list(ids_set), f, ensure_ascii=False, indent=4)
    except IOError as e:
        logger.error(f"保存已发送ID文件失败 {file_path}: {e}")

# 初始化已发送ID集合
SENT_IDS_FILE = os.path.join(os.path.dirname(__file__), "sent_restaurant_ids.json")
_sent_restaurant_ids = load_sent_ids(SENT_IDS_FILE)

# --- 核心功能函数 ---

def fetch_html(url: str, headers: dict) -> str | None:
    """
    纯函数：根据URL和请求头获取网页的HTML内容。
    """
    try:
        logger.info(f"正在请求: {url}")
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"请求 {url} 失败: {e}")
        return None

def parse_html_for_restaurant_jobs(html_content: str, base_url: str, search_terms: list) -> list[dict]:
    """
    纯函数：解析HTML内容，提取符合条件的餐厅招聘信息。
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    jobs = []

    # 查找所有包含招聘信息的表格行
    topic_rows = soup.find_all('tr', class_='bg_small_yellow')

    for row in topic_rows:
        # 在每行中查找包含标题的链接
        title_link = row.find('a', href=True)
        if title_link:
            title = title_link.get_text(strip=True)
            relative_link = title_link.get('href')

            # 拼接完整链接
            full_link = relative_link
            if relative_link and not relative_link.startswith(('http://', 'https://')):
                domain_base = "https://c.dadi360.com"
                full_link = f"{domain_base}{relative_link}" if relative_link.startswith('/') else f"{domain_base}/{relative_link}"

            # 检查是否包含任意一个搜索关键词
            if any(search_term in title for search_term in search_terms):
                # 提取发帖人和日期信息
                author_cell = row.find('td', class_='row3')
                author = ""
                if author_cell:
                    author_link = author_cell.find('a')
                    if author_link:
                        author = author_link.get_text(strip=True)
                    else:
                        author = author_cell.get_text(strip=True)

                date_cell = row.find('td', class_='row3', attrs={'nowrap': 'nowrap'})
                post_date = ""
                if date_cell:
                    # 首先尝试查找span标签中的日期
                    date_span = date_cell.find('span', class_='postdetails')
                    if date_span:
                        post_date = date_span.get_text(strip=True)
                    else:
                        # 如果没有span标签，直接获取td的文本内容
                        post_date = date_cell.get_text(strip=True)
                    
                    # 如果日期为空，尝试其他方式查找
                    if not post_date:
                        # 查找所有td，寻找包含日期格式的单元格
                        all_cells = row.find_all('td')
                        for cell in all_cells:
                            cell_text = cell.get_text(strip=True)
                            # 检查是否包含日期格式 (MM/DD/YYYY 或 M/D/YYYY)
                            if re.search(r'\d{1,2}/\d{1,2}/\d{4}', cell_text):
                                post_date = cell_text
                                break

                jobs.append({
                    'title': title,
                    'link': full_link,
                    'author': author,
                    'date': post_date
                })
                logger.info(f"找到匹配招聘信息: {title}")
    
    return jobs

def filter_new_jobs(all_jobs: list[dict], existing_ids: set) -> tuple[list[dict], set]:
    """
    纯函数：从所有招聘信息中过滤出新的信息，并更新已发送ID集合。
    """
    new_jobs = []
    updated_ids = set(existing_ids)

    for job in all_jobs:
        unique_id = f"{job['title']}-{job['link']}"
        if unique_id not in updated_ids:
            new_jobs.append(job)
            updated_ids.add(unique_id)
            logger.info(f"发现新招聘信息: {job['title']}")
    return new_jobs, updated_ids

def format_email_body(jobs: list[dict], search_terms: list) -> tuple[str, str]:
    """
    纯函数：根据招聘信息列表格式化邮件主题和内容。
    """
    search_terms_str = "、".join(search_terms[:3])
    subject = f"【餐厅招聘】{search_terms_str}等招聘信息通知"
    
    # 生成统计总结
    summary = summarize_jobs_by_date(jobs)
    
    body = f"你好！\n\n我们发现以下新的餐厅招聘信息（匹配关键词：{', '.join(search_terms)}）：\n"
    body += summary  # 添加统计总结
    
    for idx, job in enumerate(jobs):
        body += f"{idx + 1}. 📅 发布日期: {job['date']}\n"
        body += f"   📝 标题: {job['title']}\n"
        body += f"   👤 发帖人: {job['author']}\n"
        body += f"   🔗 链接: {job['link']}\n"
        if 'desc' in job and job['desc']:
            body += f"   📄 详情: {job['desc']}\n"
        body += "   " + "─" * 50 + "\n"
    
    body += "\n请尽快查看！\n\n"
    body += f"通知时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    return subject, body

def send_email(email_config: dict, subject: str, body: str) -> None:
    """
    函数：发送邮件通知。
    """
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = email_config["SENDER_EMAIL"]
    msg['To'] = email_config["RECEIVER_EMAIL"]

    try:
        if email_config["SMTP_PORT"] == 465:
            server = smtplib.SMTP_SSL(email_config["SMTP_SERVER"], email_config["SMTP_PORT"])
        else:
            server = smtplib.SMTP(email_config["SMTP_SERVER"], email_config["SMTP_PORT"])
            server.starttls()
        
        server.login(email_config["SENDER_EMAIL"], email_config["SENDER_PASSWORD"])
        server.send_message(msg)
        server.quit()
        logger.success(f"邮件已发送到 {email_config['RECEIVER_EMAIL']}")
    except Exception as e:
        logger.error(f"发送邮件失败: {e}")
        logger.error(f"请检查邮箱配置：发件人邮箱、密码、SMTP服务器和端口。")

def fetch_job_description(job_url: str, headers: dict) -> str:
    """获取招聘信息的详细描述"""
    html = fetch_html(job_url, headers)
    if not html:
        return ""
    soup = BeautifulSoup(html, 'html.parser')
    postbody = soup.find('div', class_='postbody')
    if postbody:
        return postbody.get_text(separator='\n', strip=True)
    return ""

def summarize_jobs_by_date(jobs: list[dict]) -> str:
    """
    按日期统计工作数量并生成总结
    """
    from collections import defaultdict
    from datetime import datetime
    import re
    
    # 按日期分组统计
    date_counts = defaultdict(int)
    total_jobs = len(jobs)
    
    for job in jobs:
        date_str = job.get('date', '')
        if date_str:
            # 尝试解析日期
            try:
                # 处理常见的日期格式
                date_patterns = [
                    r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2024-01-15
                    r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 01/15/2024 或 1/15/2024
                    r'(\d{1,2})-(\d{1,2})-(\d{4})',  # 01-15-2024
                    r'(\d{4})/(\d{1,2})/(\d{1,2})',  # 2024/01/15
                ]
                
                parsed_date = None
                for pattern in date_patterns:
                    match = re.search(pattern, date_str.strip())
                    if match:
                        if len(match.group(1)) == 4:  # 年份在前
                            year, month, day = match.groups()
                        else:  # 月份在前
                            month, day, year = match.groups()
                        
                        # 确保月日都是两位数
                        month = month.zfill(2)
                        day = day.zfill(2)
                        
                        parsed_date = datetime(int(year), int(month), int(day))
                        break
                
                if parsed_date:
                    # 格式化日期为 YYYY-MM-DD
                    formatted_date = parsed_date.strftime('%Y-%m-%d')
                    date_counts[formatted_date] += 1
                else:
                    # 如果无法解析，使用原始日期字符串
                    date_counts[date_str] += 1
                    
            except Exception as e:
                logger.warning(f"解析日期失败 '{date_str}': {e}")
                date_counts[date_str] += 1
        else:
            # 没有日期的归为"未知日期"
            date_counts["未知日期"] += 1
    
    # 生成统计总结
    summary = f"\n📊 工作统计总结:\n"
    summary += f"总工作数量: {total_jobs} 个\n"
    summary += f"按日期分布:\n"
    
    if date_counts:
        # 按日期排序（未知日期放在最后）
        sorted_dates = sorted(
            date_counts.items(),
            key=lambda x: (x[0] == "未知日期", x[0])
        )
        
        for date, count in sorted_dates:
            summary += f"  • {date}: {count} 个工作\n"
    else:
        summary += f"  • 暂无日期信息\n"
    
    summary += f"\n"
    return summary

# --- 主协调函数 ---

def scrape_and_notify_restaurant_jobs(config: dict, current_sent_ids: set) -> set:
    """
    主协调函数：执行餐厅招聘信息抓取、筛选和通知的整个流程。
    """
    try:
        logger.info(f"--- 餐厅招聘监控任务开始: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
        all_raw_jobs = []

        # 餐厅招聘页面的URL模式
        restaurant_urls = [
            "https://c.dadi360.com/c/forums/show//57.page",  # 第1页
            "https://c.dadi360.com/c/forums/show/90/57.page",  # 第2页
            "https://c.dadi360.com/c/forums/show/180/57.page",  # 第3页
            "https://c.dadi360.com/c/forums/show/270/57.page",  # 第4页
            "https://c.dadi360.com/c/forums/show/360/57.page"   # 第5页
        ]

        for page_num, page_url in enumerate(restaurant_urls, 1):
            try:
                logger.info(f"正在抓取第 {page_num} 页: {page_url}")
                html_content = fetch_html(page_url, config["HEADERS"])
                if html_content:
                    # 使用餐厅招聘关键词
                    restaurant_keywords = config.get("restaurant_jobs", {}).get("keywords", ["餐厅", "餐馆", "厨师", "企台", "收银", "打杂", "油锅", "寿司", "铁板", "外卖"])
                    jobs_on_page = parse_html_for_restaurant_jobs(
                        html_content, page_url, restaurant_keywords
                    )
                    all_raw_jobs.extend(jobs_on_page)
                else:
                    logger.warning(f"第 {page_num} 页抓取失败，跳过")
            except Exception as e:
                logger.error(f"抓取第 {page_num} 页时出错: {e}")
                continue
            
            time.sleep(2)  # 礼貌性延迟

        # 过滤出新招聘信息并更新已发送ID集合
        try:
            new_jobs, updated_sent_ids = filter_new_jobs(all_raw_jobs, current_sent_ids)
        except Exception as e:
            logger.error(f"过滤招聘信息时出错: {e}")
            return current_sent_ids

        # 获取每个新招聘信息的详细描述
        for job in new_jobs:
            try:
                job['desc'] = fetch_job_description(job['link'], config["HEADERS"])
            except Exception as e:
                logger.warning(f"获取招聘详情失败: {e}")
                job['desc'] = "详情获取失败"

        # 根据发布日期排序，最新的排在前面
        try:
            def parse_date(date_str):
                """解析日期字符串，返回可比较的日期对象"""
                if not date_str:
                    return None
                try:
                    # 处理常见的日期格式
                    from datetime import datetime
                    
                    # 移除多余的空格
                    date_str = date_str.strip()
                    
                    # 尝试解析不同的日期格式
                    date_patterns = [
                        r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2024-01-15
                        r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 01/15/2024 或 1/15/2024
                        r'(\d{1,2})-(\d{1,2})-(\d{4})',  # 01-15-2024
                        r'(\d{4})/(\d{1,2})/(\d{1,2})',  # 2024/01/15
                    ]
                    
                    for pattern in date_patterns:
                        match = re.search(pattern, date_str)
                        if match:
                            if len(match.group(1)) == 4:  # 年份在前
                                year, month, day = match.groups()
                            else:  # 月份在前
                                month, day, year = match.groups()
                            
                            # 确保月日都是两位数
                            month = month.zfill(2)
                            day = day.zfill(2)
                            
                            return datetime(int(year), int(month), int(day))
                    
                    # 如果无法解析，返回None
                    return None
                except:
                    return None
            
            # 按日期排序，最新的在前
            def sort_key(job):
                """排序键函数，处理None日期"""
                date_obj = parse_date(job.get('date', ''))
                # 如果日期为None，返回一个很早的日期作为fallback
                if date_obj is None:
                    from datetime import datetime
                    return (datetime(1900, 1, 1), 0)  # 很早的日期，排在最后
                return (date_obj, 0)  # 正常日期
            
            new_jobs.sort(key=sort_key, reverse=True)
            
            # 移除无法解析日期的项目（放在最后）
            valid_jobs = [job for job in new_jobs if parse_date(job.get('date', '')) is not None]
            invalid_jobs = [job for job in new_jobs if parse_date(job.get('date', '')) is None]
            new_jobs = valid_jobs + invalid_jobs
        except Exception as e:
            logger.error(f"排序招聘信息时出错: {e}")

        if new_jobs:
            # 格式化邮件内容
            try:
                restaurant_keywords = config.get("restaurant_jobs", {}).get("keywords", ["餐厅", "餐馆", "厨师", "企台", "收银", "打杂", "油锅", "寿司", "铁板", "外卖"])
                
                # 生成并记录统计信息
                summary = summarize_jobs_by_date(new_jobs)
                logger.info(f"📊 发现新工作统计: {summary.strip()}")
                
                subject, body = format_email_body(new_jobs, restaurant_keywords)
                
                # 打印邮件内容预览
                logger.info(f"\n📧 邮件预览:")
                logger.info(f"主题: {subject}")
                logger.info(f"收件人: {config['EMAIL']['RECEIVER_EMAIL']}")
                logger.info(f"内容:\n{body}")
                logger.info(f"--- 邮件预览结束 ---\n")
                
                # 发送邮件
                send_email(config["EMAIL"], subject, body)
            except Exception as e:
                logger.error(f"发送邮件时出错: {e}")
        else:
            try:
                restaurant_keywords = config.get("restaurant_jobs", {}).get("keywords", ["餐厅", "餐馆", "厨师", "企台", "收银", "打杂", "油锅", "寿司", "铁板", "外卖"])
                search_terms_str = "、".join(restaurant_keywords[:3])
                logger.info(f"此次任务未发现新的 '{search_terms_str}等' 招聘信息。")
            except Exception as e:
                logger.error(f"处理无新信息时出错: {e}")
        
        logger.info(f"--- 餐厅招聘监控任务结束: {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        return updated_sent_ids
        
    except Exception as e:
        logger.error(f"餐厅招聘监控任务发生严重错误: {e}")
        logger.error(f"程序将继续运行，等待下次调度...")
        return current_sent_ids

# --- 调度器设置和主入口 ---

def scheduled_task():
    """调度任务函数"""
    global _sent_restaurant_ids
    try:
        _sent_restaurant_ids = scrape_and_notify_restaurant_jobs(CONFIG, _sent_restaurant_ids)
        save_sent_ids(SENT_IDS_FILE, _sent_restaurant_ids)
    except Exception as e:
        logger.error(f"调度任务发生严重错误: {e}")
        logger.error(f"程序将继续运行，等待下次调度...")
        # 即使出错也要保存当前状态
        try:
            save_sent_ids(SENT_IDS_FILE, _sent_restaurant_ids)
        except Exception as save_error:
            logger.error(f"保存状态失败: {save_error}")

if __name__ == "__main__":
    try:
        logger.info("餐厅招聘监控脚本已启动。")
        restaurant_config = CONFIG.get("restaurant_jobs", {})
        keywords = restaurant_config.get("keywords", ["餐厅", "餐馆", "厨师", "企台", "收银", "打杂", "油锅", "寿司", "铁板", "外卖"])
        keywords_str = "、".join(keywords[:5])
        interval_seconds = restaurant_config.get("send_interval_seconds", 172800)  # 默认2天
        interval_hours = interval_seconds // 3600  # 转换为小时
        
        logger.info(f"将每{interval_hours}小时检查一次餐厅招聘页面的前5页，查找: {keywords_str}")
        logger.info(f"通知将发送到: {CONFIG['EMAIL']['RECEIVER_EMAIL']}")
        logger.info("按 Ctrl+C 停止脚本。")

        # 创建调度器
        scheduler = Scheduler()
        
        # 立即执行一次
        scheduled_task()
        
        # 添加定时任务
        scheduler.every(interval_seconds, scheduled_task)
        
        # 启动调度器
        scheduler.start()
        
        try:
            # 保持主线程运行
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n正在停止餐厅招聘监控脚本...")
            scheduler.stop()
            logger.info("脚本已停止。")
            
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        logger.error("请检查配置文件和相关设置。") 