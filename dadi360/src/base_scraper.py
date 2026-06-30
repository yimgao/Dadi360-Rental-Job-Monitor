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
from abc import ABC, abstractmethod
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime
from collections import defaultdict

# 抑制SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BaseScraper(ABC):
    """
    基础抓取器类，包含所有共享功能
    子类只需要实现特定的解析逻辑
    """
    
    def __init__(self, config: Dict, scraper_name: str, sent_ids_file: str):
        """
        初始化基础抓取器
        
        Args:
            config: 配置字典
            scraper_name: 抓取器名称（用于日志文件名）
            sent_ids_file: 已发送ID文件路径
        """
        self.config = config
        self.scraper_name = scraper_name
        self.sent_ids_file = sent_ids_file
        
        # 获取项目根目录
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.logs_dir = os.path.join(self.project_root, "logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        
        self.sent_ids = self._load_sent_ids()
        
        # 设置日志
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志配置"""
        logger.remove()  # 移除默认处理器
        
        # 信息日志
        logger.add(
            os.path.join(self.logs_dir, f"{self.scraper_name}_info.log"),
            rotation="10 MB",
            retention="30 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            encoding="utf-8",
            filter=lambda record: record["level"].name in ["INFO", "SUCCESS", "WARNING"]
        )
        
        # 错误日志
        logger.add(
            os.path.join(self.logs_dir, f"{self.scraper_name}_error.log"),
            rotation="5 MB",
            retention="60 days",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            encoding="utf-8",
            filter=lambda record: record["level"].name in ["ERROR", "CRITICAL"]
        )
        
        # 控制台输出
        logger.add(
            sys.stdout,
            level="INFO",
            format="{time:HH:mm:ss} | {level} | {message}",
            colorize=True
        )
    
    def _load_sent_ids(self) -> Set[str]:
        """从文件中加载已发送的ID集合"""
        if os.path.exists(self.sent_ids_file):
            try:
                with open(self.sent_ids_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"加载已发送ID文件失败 {self.sent_ids_file}: {e}. 初始化为空集合。")
                return set()
        return set()
    
    def _save_sent_ids(self):
        """将已发送的ID集合保存到文件"""
        try:
            with open(self.sent_ids_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.sent_ids), f, ensure_ascii=False, indent=4)
        except IOError as e:
            logger.error(f"保存已发送ID文件失败 {self.sent_ids_file}: {e}")
    
    def fetch_html(self, url: str) -> Optional[str]:
        """获取网页HTML内容"""
        try:
            logger.info(f"正在请求: {url}")
            response = requests.get(url, headers=self.config["HEADERS"], timeout=15, verify=False)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"请求 {url} 失败: {e}")
            return None
    
    def fetch_job_description(self, job_url: str) -> str:
        """获取招聘信息的详细描述"""
        html = self.fetch_html(job_url)
        if not html:
            return ""
        soup = BeautifulSoup(html, 'html.parser')
        postbody = soup.find('div', class_='postbody')
        if postbody:
            return postbody.get_text(separator='\n', strip=True)
        return ""
    
    def filter_new_jobs(self, all_jobs: List[Dict]) -> Tuple[List[Dict], Set[str]]:
        """过滤出新招聘信息并更新已发送ID集合"""
        new_jobs = []
        updated_ids = set(self.sent_ids)
        
        for job in all_jobs:
            unique_id = f"{job['title']}-{job['link']}"
            if unique_id not in updated_ids:
                new_jobs.append(job)
                updated_ids.add(unique_id)
                logger.info(f"发现新招聘信息: {job['title']}")
        
        return new_jobs, updated_ids
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串，返回可比较的日期对象"""
        if not date_str:
            return None
        try:
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
    
    def sort_jobs_by_date(self, jobs: List[Dict]) -> List[Dict]:
        """根据发布日期排序，最新的排在前面"""
        try:
            def sort_key(job):
                """排序键函数，处理None日期"""
                date_obj = self.parse_date(job.get('date', ''))
                # 如果日期为None，返回一个很早的日期作为fallback
                if date_obj is None:
                    return (datetime(1900, 1, 1), 0)  # 很早的日期，排在最后
                return (date_obj, 0)  # 正常日期
            
            jobs.sort(key=sort_key, reverse=True)
            
            # 移除无法解析日期的项目（放在最后）
            valid_jobs = [job for job in jobs if self.parse_date(job.get('date', '')) is not None]
            invalid_jobs = [job for job in jobs if self.parse_date(job.get('date', '')) is None]
            return valid_jobs + invalid_jobs
        except Exception as e:
            logger.error(f"排序招聘信息时出错: {e}")
            return jobs
    
    def summarize_jobs_by_date(self, jobs: List[Dict]) -> str:
        """按日期统计工作数量并生成总结"""
        # 按日期分组统计
        date_counts = defaultdict(int)
        total_jobs = len(jobs)
        
        for job in jobs:
            date_str = job.get('date', '')
            if date_str:
                # 尝试解析日期
                try:
                    parsed_date = self.parse_date(date_str)
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
    
    def format_email_body(self, jobs: List[Dict], search_terms: List[str]) -> Tuple[str, str]:
        """根据招聘信息列表格式化邮件主题和内容"""
        search_terms_str = "、".join(search_terms[:3])
        subject = f"【{self.get_email_subject_prefix()}】{search_terms_str}等招聘信息通知"
        
        # 生成统计总结
        summary = self.summarize_jobs_by_date(jobs)
        
        body = f"你好！\n\n我们发现以下新的{self.get_job_type_name()}招聘信息（匹配关键词：{', '.join(search_terms)}）：\n"
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
    
    def send_email(self, subject: str, body: str):
        """发送邮件通知"""
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = self.config["EMAIL"]["SENDER_EMAIL"]
        msg['To'] = self.config["EMAIL"]["RECEIVER_EMAIL"]

        try:
            if self.config["EMAIL"]["SMTP_PORT"] == 465:
                server = smtplib.SMTP_SSL(self.config["EMAIL"]["SMTP_SERVER"], self.config["EMAIL"]["SMTP_PORT"])
            else:
                server = smtplib.SMTP(self.config["EMAIL"]["SMTP_SERVER"], self.config["EMAIL"]["SMTP_PORT"])
                server.starttls()
            
            server.login(self.config["EMAIL"]["SENDER_EMAIL"], self.config["EMAIL"]["SENDER_PASSWORD"])
            server.send_message(msg)
            server.quit()
            logger.success(f"邮件已发送到 {self.config['EMAIL']['RECEIVER_EMAIL']}")
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            logger.error(f"请检查邮箱配置：发件人邮箱、密码、SMTP服务器和端口。")
    
    def scrape_and_notify(self) -> Set[str]:
        """主协调函数：执行招聘信息抓取、筛选和通知的整个流程"""
        try:
            logger.info(f"--- {self.get_job_type_name()}招聘监控任务开始: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
            all_raw_jobs = []

            # 获取页面URL列表
            urls = self.get_target_urls()

            for page_num, page_url in enumerate(urls, 1):
                try:
                    logger.info(f"正在抓取第 {page_num} 页: {page_url}")
                    html_content = self.fetch_html(page_url)
                    if html_content:
                        # 获取搜索关键词
                        keywords = self.get_search_keywords()
                        jobs_on_page = self.parse_html_for_jobs(html_content, page_url, keywords)
                        all_raw_jobs.extend(jobs_on_page)
                    else:
                        logger.warning(f"第 {page_num} 页抓取失败，跳过")
                except Exception as e:
                    logger.error(f"抓取第 {page_num} 页时出错: {e}")
                    continue
                
                time.sleep(2)  # 礼貌性延迟

            # 过滤出新招聘信息并更新已发送ID集合
            try:
                new_jobs, updated_sent_ids = self.filter_new_jobs(all_raw_jobs)
            except Exception as e:
                logger.error(f"过滤招聘信息时出错: {e}")
                return self.sent_ids

            # 获取每个新招聘信息的详细描述
            for job in new_jobs:
                try:
                    job['desc'] = self.fetch_job_description(job['link'])
                except Exception as e:
                    logger.warning(f"获取招聘详情失败: {e}")
                    job['desc'] = "详情获取失败"

            # 根据发布日期排序，最新的排在前面
            new_jobs = self.sort_jobs_by_date(new_jobs)

            if new_jobs:
                # 格式化邮件内容
                try:
                    keywords = self.get_search_keywords()
                    
                    # 生成并记录统计信息
                    summary = self.summarize_jobs_by_date(new_jobs)
                    logger.info(f"📊 发现新工作统计: {summary.strip()}")
                    
                    subject, body = self.format_email_body(new_jobs, keywords)
                    
                    # 打印邮件内容预览
                    logger.info(f"\n📧 邮件预览:")
                    logger.info(f"主题: {subject}")
                    logger.info(f"收件人: {self.config['EMAIL']['RECEIVER_EMAIL']}")
                    logger.info(f"内容:\n{body}")
                    logger.info(f"--- 邮件预览结束 ---\n")
                    
                    # 发送邮件
                    self.send_email(subject, body)
                except Exception as e:
                    logger.error(f"发送邮件时出错: {e}")
            else:
                try:
                    keywords = self.get_search_keywords()
                    search_terms_str = "、".join(keywords[:3])
                    logger.info(f"此次任务未发现新的 '{search_terms_str}等' 招聘信息。")
                except Exception as e:
                    logger.error(f"处理无新信息时出错: {e}")
            
            logger.info(f"--- {self.get_job_type_name()}招聘监控任务结束: {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            return updated_sent_ids
            
        except Exception as e:
            logger.error(f"{self.get_job_type_name()}招聘监控任务发生严重错误: {e}")
            logger.error(f"程序将继续运行，等待下次调度...")
            return self.sent_ids
    
    def run_scheduled_task(self):
        """调度任务函数"""
        try:
            self.sent_ids = self.scrape_and_notify()
            self._save_sent_ids()
        except Exception as e:
            logger.error(f"调度任务发生严重错误: {e}")
            logger.error(f"程序将继续运行，等待下次调度...")
            # 即使出错也要保存当前状态
            try:
                self._save_sent_ids()
            except Exception as save_error:
                logger.error(f"保存状态失败: {save_error}")
    
    # 抽象方法 - 子类必须实现
    @abstractmethod
    def get_target_urls(self) -> List[str]:
        """获取目标URL列表"""
        pass
    
    @abstractmethod
    def get_search_keywords(self) -> List[str]:
        """获取搜索关键词列表"""
        pass
    
    @abstractmethod
    def parse_html_for_jobs(self, html_content: str, base_url: str, search_terms: List[str]) -> List[Dict]:
        """解析HTML内容，提取符合条件的招聘信息"""
        pass
    
    @abstractmethod
    def get_job_type_name(self) -> str:
        """获取工作类型名称（用于日志和邮件）"""
        pass
    
    @abstractmethod
    def get_email_subject_prefix(self) -> str:
        """获取邮件主题前缀"""
        pass 