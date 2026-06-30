#!/usr/bin/env python3
"""
租房信息抓取脚本 - 重构版本
继承BaseScraper类，减少代码重复
"""

import os
import json
import time
import sys
from bs4 import BeautifulSoup
from loguru import logger
import re

# 添加父目录到路径，以便导入base_scraper
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from base_scraper import BaseScraper
from scheduler_util import Scheduler

class RentalScraper(BaseScraper):
    """租房信息抓取器"""
    
    def __init__(self, config: dict):
        """初始化租房抓取器"""
        sent_ids_file = os.path.join(os.path.dirname(__file__), "sent_listing_ids.json")
        super().__init__(config, "rental", sent_ids_file)
    
    def get_target_urls(self) -> list[str]:
        """获取租房页面的URL列表"""
        return [
            "https://c.dadi360.com/c/forums/show/87.page",  # 第1页
            "https://c.dadi360.com/c/forums/show/90/87.page",  # 第2页
            "https://c.dadi360.com/c/forums/show/180/87.page",  # 第3页
            "https://c.dadi360.com/c/forums/show/270/87.page",  # 第4页
            "https://c.dadi360.com/c/forums/show/360/87.page"   # 第5页
        ]
    
    def get_search_keywords(self) -> list[str]:
        """获取租房搜索关键词"""
        return self.config.get("rental", {}).get("keywords", [
            "出租", "租房", "房屋出租", "公寓出租", "房间出租", "整租", "分租", 
            "单间", "一室", "两室", "三室", "studio", "1b1b", "2b1b", "3b1b",
            "地铁", "近地铁", "交通便利", "包水电网", "包水电", "包网", "不包",
            "长租", "短租", "月租", "年租", "押金", "deposit", "rent", "lease"
        ])
    
    def parse_html_for_jobs(self, html_content: str, base_url: str, search_terms: list[str]) -> list[dict]:
        """解析HTML内容，提取符合条件的租房信息"""
        soup = BeautifulSoup(html_content, 'html.parser')
        listings = []

        # 查找所有包含租房信息的表格行
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
                    logger.info(f"找到匹配租房信息: {title}")
        
        return listings
    
    def get_job_type_name(self) -> str:
        """获取工作类型名称"""
        return "租房"
    
    def get_email_subject_prefix(self) -> str:
        """获取邮件主题前缀"""
        return "租房信息"

def main():
    """主函数"""
    try:
        # 加载配置
        config_path = os.path.join(os.path.dirname(__file__), '../../config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 创建租房抓取器
        scraper = RentalScraper(config)
        
        logger.info("租房监控脚本已启动。")
        keywords = scraper.get_search_keywords()
        keywords_str = "、".join(keywords[:5])
        interval_seconds = config.get("rental", {}).get("send_interval_seconds", 172800)  # 默认2天
        interval_hours = interval_seconds // 3600  # 转换为小时
        
        logger.info(f"将每{interval_hours}小时检查一次租房页面的前5页，查找: {keywords_str}")
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
            logger.info("\n正在停止租房监控脚本...")
            scheduler.stop()
            logger.info("脚本已停止。")
            
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        logger.error("请检查配置文件和相关设置。")

if __name__ == "__main__":
    main() 