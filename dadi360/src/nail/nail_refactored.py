#!/usr/bin/env python3
"""
美甲招聘信息抓取脚本 - 重构版本
继承BaseScraper类，减少代码重复
"""

import os
import json
import time
import sys
from bs4 import BeautifulSoup
from loguru import logger
import re # Added missing import for re

# 添加父目录到路径，以便导入base_scraper
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from base_scraper import BaseScraper
from scheduler_util import Scheduler

class NailJobScraper(BaseScraper):
    """美甲招聘信息抓取器"""
    
    def __init__(self, config: dict):
        """初始化美甲招聘抓取器"""
        sent_ids_file = os.path.join(os.path.dirname(__file__), "sent_nail_ids.json")
        super().__init__(config, "nail_jobs", sent_ids_file)
    
    def get_target_urls(self) -> list[str]:
        """获取美甲招聘页面的URL列表"""
        return [
            "https://c.dadi360.com/c/forums/show/56.page",  # 第1页
            "https://c.dadi360.com/c/forums/show/90/56.page",  # 第2页
            "https://c.dadi360.com/c/forums/show/180/56.page",  # 第3页
            "https://c.dadi360.com/c/forums/show/270/56.page",  # 第4页
            "https://c.dadi360.com/c/forums/show/360/56.page"   # 第5页
        ]
    
    def get_search_keywords(self) -> list[str]:
        """获取美甲招聘搜索关键词"""
        return self.config.get("nail_jobs", {}).get("keywords", [
            "美甲", "指甲", "nail", "甲店", "美甲师", "指甲师", "美甲店", "指甲店", 
            "美甲工作", "指甲工作", "美甲请人", "指甲请人", "美甲招聘", "指甲招聘", 
            "美甲师招聘", "指甲师招聘", "美甲学徒", "指甲学徒", "美甲助理", "指甲助理", 
            "美甲师傅", "指甲师傅", "美甲店请人", "指甲店请人", "美甲店招聘", "指甲店招聘", 
            "小工", "大工"
        ])
    
    def parse_html_for_jobs(self, html_content: str, base_url: str, search_terms: list[str]) -> list[dict]:
        """解析HTML内容，提取符合条件的美甲招聘信息"""
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
    
    def get_job_type_name(self) -> str:
        """获取工作类型名称"""
        return "美甲"
    
    def get_email_subject_prefix(self) -> str:
        """获取邮件主题前缀"""
        return "美甲招聘"

def main():
    """主函数"""
    try:
        # 加载配置
        config_path = os.path.join(os.path.dirname(__file__), '../../config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 创建美甲招聘抓取器
        scraper = NailJobScraper(config)
        
        logger.info("美甲招聘监控脚本已启动。")
        keywords = scraper.get_search_keywords()
        keywords_str = "、".join(keywords[:5])
        interval_seconds = config.get("nail_jobs", {}).get("send_interval_seconds", 172800)  # 默认2天
        interval_hours = interval_seconds // 3600  # 转换为小时
        
        logger.info(f"将每{interval_hours}小时检查一次美甲招聘页面的前5页，查找: {keywords_str}")
        logger.info(f"通知将发送到: {config['EMAIL']['RECEIVER_EMAIL']}")
        logger.info("按 Ctrl+C 停止脚本。")

        # 创建调度器
        scheduler = Scheduler()
        
        # 立即执行一次
        scraper.run_scheduled_task()
        
        # 添加定时任务
        scheduler.every(interval_seconds, scraper.run_scheduled_task)
        
        # 启动调度器
        scheduler.start()
        
        try:
            # 保持主线程运行
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n正在停止美甲招聘监控脚本...")
            scheduler.stop()
            logger.info("脚本已停止。")
            
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        logger.error("请检查配置文件和相关设置。")

if __name__ == "__main__":
    main() 