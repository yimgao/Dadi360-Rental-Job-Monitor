import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import time
import schedule
import os
import json # 用于持久化已发送的房源 ID
import urllib3 # 用于抑制SSL警告
from loguru import logger
import sys
import re # 用于日期匹配
from collections import defaultdict
from datetime import datetime

# 配置loguru日志
logger.remove()  # 移除默认处理器

# 获取项目根目录的绝对路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# 信息日志 - 记录所有INFO及以上级别的日志
logger.add(
    os.path.join(LOGS_DIR, "rental_info.log"),
    rotation="10 MB",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    encoding="utf-8",
    filter=lambda record: record["level"].name in ["INFO", "SUCCESS", "WARNING"]
)

# 错误日志 - 只记录ERROR及以上级别的日志
logger.add(
    os.path.join(LOGS_DIR, "rental_error.log"),
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
    """从文件中加载已发送的房源ID集合。"""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"加载已发送ID文件失败 {file_path}: {e}. 初始化为空集合。")
            return set()
    return set()

def save_sent_ids(file_path, ids_set):
    """将已发送的房源ID集合保存到文件。"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(list(ids_set), f, ensure_ascii=False, indent=4)
    except IOError as e:
        logger.error(f"保存已发送ID文件失败 {file_path}: {e}")

# 初始化已发送ID集合
# 这是一个外部状态，但在主函数中会通过参数传递，尽量减少直接依赖
SENT_IDS_FILE = os.path.join(os.path.dirname(__file__), "sent_listing_ids.json")
_sent_listing_ids = load_sent_ids(SENT_IDS_FILE)


# --- 核心功能函数 ---

def fetch_html(url: str, headers: dict) -> str | None:
    """
    纯函数：根据URL和请求头获取网页的HTML内容。
    - 输入：url, headers
    - 输出：HTML字符串或None
    - 副作用：无
    """
    try:
        logger.info(f"正在请求: {url}")
        # 添加 verify=False 来跳过SSL证书验证
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"请求 {url} 失败: {e}")
        return None

def parse_html_for_listings(html_content: str, base_url: str, search_terms: list) -> list[dict]:
    """
    纯函数：解析HTML内容，提取符合条件的房源信息。
    - 输入：HTML字符串, 网站基础URL, 搜索关键词列表
    - 输出：符合条件的房源列表 (每个元素是 {'title': '...', 'link': '...', 'author': '...', 'date': '...'})
    - 副作用：无
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    listings = []

    # 查找所有包含房源信息的表格行
    # 每个房源都在 <tr class="bg_small_yellow"> 中
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

                listings.append({
                    'title': title,
                    'link': full_link,
                    'author': author,
                    'date': post_date
                })
                logger.info(f"找到匹配房源: {title}")
    
    return listings

def filter_new_listings(all_listings: list[dict], existing_ids: set) -> tuple[list[dict], set]:
    """
    纯函数：从所有房源中过滤出新的房源，并更新已发送ID集合。
    - 输入：所有房源列表, 当前已发送ID集合
    - 输出：新房源列表, 更新后的已发送ID集合
    - 副作用：无 (但会返回一个新的集合，而不是修改原集合)
    """
    new_listings = []
    updated_ids = set(existing_ids) # 复制一份，确保不修改原始传入的集合

    for listing in all_listings:
        unique_id = f"{listing['title']}-{listing['link']}"
        if unique_id not in updated_ids:
            new_listings.append(listing)
            updated_ids.add(unique_id)
            logger.info(f"发现新房源: {listing['title']}")
    return new_listings, updated_ids

def format_email_body(listings: list[dict], search_terms: list) -> tuple[str, str]:
    """
    纯函数：根据房源列表格式化邮件主题和内容。
    - 输入：房源列表, 搜索关键词列表
    - 输出：(主题字符串, 内容字符串)
    - 副作用：无
    """
    search_terms_str = "、".join(search_terms[:3])  # 只显示前3个关键词，避免主题过长
    subject = f"【新发现】{search_terms_str}等房源通知"
    
    # 生成统计总结
    summary = summarize_listings(listings)
    
    body = f"你好！\n\n我们发现以下新的房源信息（匹配关键词：{', '.join(search_terms)}）：\n"
    body += summary  # 添加统计总结
    
    for idx, item in enumerate(listings):
        body += f"{idx + 1}. 📅 发布日期: {item.get('date', '未知')}\n"
        body += f"   📝 标题: {item['title']}\n"
        body += f"   👤 发帖人: {item.get('author', '未知')}\n"
        body += f"   🔗 链接: {item['link']}\n"
        if 'desc' in item and item['desc']:
            body += f"   📄 详情: {item['desc']}\n"
        body += "   " + "─" * 50 + "\n"
    body += "\n请尽快查看！\n\n"
    body += f"通知时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    return subject, body

def send_email(email_config: dict, subject: str, body: str) -> None:
    """
    函数：发送邮件通知。这是一个有副作用的函数（网络IO）。
    - 输入：邮件配置, 主题, 内容
    - 输出：无
    - 副作用：发送邮件
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
        logger.error(f"如果是Gmail，请确保已开启'两步验证'并生成'应用专用密码'。")

def fetch_listing_description(listing_url: str, headers: dict) -> str:
    html = fetch_html(listing_url, headers)
    if not html:
        return ""
    soup = BeautifulSoup(html, 'html.parser')
    postbody = soup.find('div', class_='postbody')
    if postbody:
        # Get the inner text, including <br> as newlines
        return postbody.get_text(separator='\n', strip=True)
    return ""

def summarize_listings(listings: list[dict]) -> str:
    """
    统计房源信息并生成总结
    """
    total_listings = len(listings)
    
    # 生成统计总结
    summary = f"\n📊 房源统计总结:\n"
    summary += f"总房源数量: {total_listings} 个\n"
    
    # 按日期分组统计
    date_counts = defaultdict(int)
    
    for listing in listings:
        date_str = listing.get('date', '')
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
    
    # 按关键词分类统计
    keyword_counts = {}
    rental_config = CONFIG.get("rental", {})
    search_terms = rental_config.get("search_terms", ["2房一厅", "两房一厅", "2卧一厅", "两卧一厅", "2室1厅", "两室一厅", "2房1厅", "两房1厅", "2卧1厅", "两卧1厅"])
    
    for listing in listings:
        title = listing.get('title', '').lower()
        for term in search_terms:
            if term.lower() in title:
                keyword_counts[term] = keyword_counts.get(term, 0) + 1
                break  # 只匹配第一个关键词
    
    # 添加日期分布统计
    if date_counts:
        summary += f"按日期分布:\n"
        # 按日期排序（未知日期放在最后）
        sorted_dates = sorted(
            date_counts.items(),
            key=lambda x: (x[0] == "未知日期", x[0])
        )
        
        for date, count in sorted_dates:
            summary += f"  • {date}: {count} 个房源\n"
    
    # 添加关键词分布统计
    if keyword_counts:
        summary += f"按关键词分布:\n"
        for keyword, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True):
            summary += f"  • {keyword}: {count} 个房源\n"
    else:
        summary += f"  • 暂无关键词匹配信息\n"
    
    summary += f"\n"
    return summary

# --- 主协调函数 ---

def scrape_and_notify_job(config: dict, current_sent_ids: set) -> set:
    """
    主协调函数：执行抓取、筛选和通知的整个流程。
    - 输入：配置字典, 当前已发送ID集合
    - 输出：更新后的已发送ID集合 (方便外部持久化)
    - 副作用：执行网络请求, 发送邮件
    """
    logger.info(f"--- 任务开始: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    all_raw_listings = []

    # 从rental配置中获取参数
    rental_config = config.get("rental", {})
    target_url_base = rental_config.get("target_url_base", "https://c.dadi360.com/c/forums/show//87.page")
    num_pages_to_scrape = rental_config.get("num_pages_to_scrape", 5)
    search_terms = rental_config.get("search_terms", ["2房一厅", "两房一厅", "2卧一厅", "两卧一厅", "2室1厅", "两室一厅", "2房1厅", "两房1厅", "2卧1厅", "两卧1厅"])

    for page_num in range(1, num_pages_to_scrape + 1):
        # 根据页码计算URL路径
        if page_num == 1:
            page_url = target_url_base
        else:
            # 每页90个帖子，所以第2页是90，第3页是180，第4页是270
            offset = (page_num - 1) * 90
            page_url = f"https://c.dadi360.com/c/forums/show/{offset}/87.page"
        
        html_content = fetch_html(page_url, config["HEADERS"])
        if html_content:
            # parse_html_for_listings 是纯函数，返回当前页所有房源
            listings_on_page = parse_html_for_listings(
                html_content, target_url_base, search_terms
            )
            all_raw_listings.extend(listings_on_page)
        
        time.sleep(2) # 礼貌性延迟

    # 过滤出新房源并更新已发送ID集合
    new_listings, updated_sent_ids = filter_new_listings(all_raw_listings, current_sent_ids)

    # ⭐⭐⭐ Fetch and attach description for each new listing
    for listing in new_listings:
        listing['desc'] = fetch_listing_description(listing['link'], config["HEADERS"])

    # 根据发布日期排序，最新的排在前面
    try:
        def parse_date(date_str):
            """解析日期字符串，返回可比较的日期对象"""
            if not date_str:
                return None
            try:
                # 处理常见的日期格式
                date_patterns = [
                    r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2024-01-15
                    r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 01/15/2024 或 1/15/2024
                    r'(\d{1,2})-(\d{1,2})-(\d{4})',  # 01-15-2024
                    r'(\d{4})/(\d{1,2})/(\d{1,2})',  # 2024/01/15
                ]
                
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
                        
                        return datetime(int(year), int(month), int(day))
                
                # 如果无法解析，返回None
                return None
            except:
                return None
        
        # 按日期排序，最新的在前
        def sort_key(listing):
            """排序键函数，处理None日期"""
            date_obj = parse_date(listing.get('date', ''))
            # 如果日期为None，返回一个很早的日期作为fallback
            if date_obj is None:
                from datetime import datetime
                return (datetime(1900, 1, 1), 0)  # 很早的日期，排在最后
            return (date_obj, 0)  # 正常日期
        
        new_listings.sort(key=sort_key, reverse=True)
        
        # 移除无法解析日期的项目（放在最后）
        valid_listings = [listing for listing in new_listings if parse_date(listing.get('date', '')) is not None]
        invalid_listings = [listing for listing in new_listings if parse_date(listing.get('date', '')) is None]
        new_listings = valid_listings + invalid_listings
    except Exception as e:
        logger.error(f"排序房源信息时出错: {e}")

    if new_listings:
        # 格式化邮件内容，也是纯函数
        subject, body = format_email_body(new_listings, search_terms)
        
        # 生成并记录统计信息
        summary = summarize_listings(new_listings)
        logger.info(f"📊 发现新房源统计: {summary.strip()}")
        
        # 打印邮件内容预览
        logger.info(f"\n📧 邮件预览:")
        logger.info(f"主题: {subject}")
        logger.info(f"收件人: {config['EMAIL']['RECEIVER_EMAIL']}")
        logger.info(f"内容:\n{body}")
        logger.info(f"--- 邮件预览结束 ---\n")
        
        # 发送邮件是有副作用的操作
        send_email(config["EMAIL"], subject, body)
    else:
        search_terms_str = "、".join(search_terms[:3])
        logger.info(f"此次任务未发现新的 '{search_terms_str}等' 房源。")
    
    logger.info(f"--- 任务结束: {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
    return updated_sent_ids # 返回更新后的 ID 集合


# --- 调度器设置和主入口 ---

if __name__ == "__main__":
    logger.info("房源监控脚本已启动。")
    rental_config = CONFIG.get("rental", {})
    search_terms = rental_config.get("search_terms", ["2房一厅", "两房一厅", "2卧一厅", "两卧一厅", "2室1厅", "两室一厅", "2房1厅", "两房1厅", "2卧1厅", "两卧1厅"])
    target_url_base = rental_config.get("target_url_base", "https://c.dadi360.com/c/forums/show//87.page")
    num_pages_to_scrape = rental_config.get("num_pages_to_scrape", 5)
    send_interval_minutes = rental_config.get("send_interval_minutes", 10)
    
    search_terms_str = "、".join(search_terms)
    logger.info(f"将每{send_interval_minutes}分钟检查一次 {target_url_base} 的前 {num_pages_to_scrape} 页，查找: {search_terms_str}")
    logger.info(f"通知将发送到: {CONFIG['EMAIL']['RECEIVER_EMAIL']}")
    logger.info("按 Ctrl+C 停止脚本。")

    # 定义一个包装函数，以便将外部状态 (sent_listing_ids) 传递给调度任务
    def scheduled_task():
        global _sent_listing_ids # 声明使用全局变量
        _sent_listing_ids = scrape_and_notify_job(CONFIG, _sent_listing_ids)
        save_sent_ids(SENT_IDS_FILE, _sent_listing_ids) # 每次任务结束后保存状态

    # 立即执行一次，然后每指定分钟执行
    scheduled_task() # 首次运行
    schedule.every(send_interval_minutes).minutes.do(scheduled_task)

    while True:
        schedule.run_pending()
        time.sleep(1)