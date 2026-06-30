#!/usr/bin/env python3
"""
通用抓取器启动器
可以启动任意一个抓取器，为将来的UI做准备
"""

import os
import json
import time
import sys
from loguru import logger
from typing import Dict, Any

# 添加当前目录到路径
sys.path.append(os.path.dirname(__file__))

from base_scraper import BaseScraper
from scheduler_util import Scheduler

class ScraperLauncher:
    """抓取器启动器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化启动器
        
        Args:
            config_path: 配置文件路径，默认为项目根目录的config.json
        """
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '../config.json')
        
        self.config_path = config_path
        self.config = self._load_config()
        self.scrapers = {}
        self.schedulers = {}
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise
    
    def register_scraper(self, scraper_name: str, scraper_class: type, config_key: str):
        """
        注册抓取器
        
        Args:
            scraper_name: 抓取器名称
            scraper_class: 抓取器类（继承自BaseScraper）
            config_key: 配置文件中对应的键名
        """
        try:
            # 创建抓取器实例
            scraper_config = {**self.config, config_key: self.config.get(config_key, {})}
            scraper = scraper_class(scraper_config)
            self.scrapers[scraper_name] = scraper
            
            logger.success(f"成功注册抓取器: {scraper_name}")
            return True
        except Exception as e:
            logger.error(f"注册抓取器 {scraper_name} 失败: {e}")
            return False
    
    def start_scraper(self, scraper_name: str, run_once: bool = False) -> bool:
        """
        启动指定的抓取器
        
        Args:
            scraper_name: 抓取器名称
            run_once: 是否只运行一次（不进入循环）
        
        Returns:
            bool: 是否成功启动
        """
        if scraper_name not in self.scrapers:
            logger.error(f"抓取器 {scraper_name} 未注册")
            return False
        
        scraper = self.scrapers[scraper_name]
        
        try:
            if run_once:
                # 只运行一次
                logger.info(f"启动 {scraper_name} 单次运行...")
                scraper.run_scheduled_task()
                logger.success(f"{scraper_name} 单次运行完成")
                return True
            else:
                # 启动调度器
                logger.info(f"启动 {scraper_name} 调度器...")
                
                # 获取调度间隔
                config_key = scraper_name.replace('_', '')  # 移除下划线
                interval_seconds = self.config.get(config_key, {}).get("send_interval_seconds", 172800)
                
                # 创建调度器
                scheduler = Scheduler()
                
                # 立即执行一次
                scraper.run_scheduled_task()
                
                # 添加定时任务
                scheduler.every(interval_seconds, scraper.run_scheduled_task)
                
                # 启动调度器
                scheduler.start()
                
                self.schedulers[scraper_name] = scheduler
                
                logger.success(f"{scraper_name} 调度器启动成功")
                return True
                
        except Exception as e:
            logger.error(f"启动抓取器 {scraper_name} 失败: {e}")
            return False
    
    def stop_scraper(self, scraper_name: str) -> bool:
        """
        停止指定的抓取器
        
        Args:
            scraper_name: 抓取器名称
        
        Returns:
            bool: 是否成功停止
        """
        if scraper_name in self.schedulers:
            try:
                self.schedulers[scraper_name].stop()
                del self.schedulers[scraper_name]
                logger.success(f"{scraper_name} 已停止")
                return True
            except Exception as e:
                logger.error(f"停止抓取器 {scraper_name} 失败: {e}")
                return False
        else:
            logger.warning(f"抓取器 {scraper_name} 未在运行")
            return False
    
    def stop_all_scrapers(self):
        """停止所有抓取器"""
        for scraper_name in list(self.schedulers.keys()):
            self.stop_scraper(scraper_name)
    
    def get_scraper_status(self) -> Dict[str, str]:
        """获取所有抓取器状态"""
        status = {}
        for scraper_name in self.scrapers.keys():
            if scraper_name in self.schedulers:
                status[scraper_name] = "运行中"
            else:
                status[scraper_name] = "已停止"
        return status
    
    def list_available_scrapers(self) -> list[str]:
        """列出所有可用的抓取器"""
        return list(self.scrapers.keys())

def main():
    """主函数 - 演示如何使用启动器"""
    try:
        # 创建启动器
        launcher = ScraperLauncher()
        
        # 注册抓取器（需要先导入相应的类）
        try:
            from nail.nail_refactored import NailJobScraper
            launcher.register_scraper("nail_jobs", NailJobScraper, "nail_jobs")
            logger.success("✅ 美甲招聘抓取器注册成功")
        except ImportError:
            logger.warning("⚠️ 美甲招聘抓取器未找到，跳过注册")
        
        try:
            from rental.rental_refactored import RentalScraper
            launcher.register_scraper("rental", RentalScraper, "rental")
            logger.success("✅ 租房抓取器注册成功")
        except ImportError:
            logger.warning("⚠️ 租房抓取器未找到，跳过注册")
        
        try:
            from restaurant.restaurant_refactored import RestaurantJobScraper
            launcher.register_scraper("restaurant_jobs", RestaurantJobScraper, "restaurant_jobs")
            logger.success("✅ 餐厅招聘抓取器注册成功")
        except ImportError:
            logger.warning("⚠️ 餐厅招聘抓取器未找到，跳过注册")
        
        # 显示可用抓取器
        available_scrapers = launcher.list_available_scrapers()
        if not available_scrapers:
            logger.error("没有可用的抓取器")
            return
        
        logger.info(f"可用的抓取器: {', '.join(available_scrapers)}")
        
        # 启动所有抓取器
        for scraper_name in available_scrapers:
            launcher.start_scraper(scraper_name)
        
        # 显示状态
        status = launcher.get_scraper_status()
        logger.info("抓取器状态:")
        for name, state in status.items():
            logger.info(f"  {name}: {state}")
        
        logger.info("所有抓取器已启动。按 Ctrl+C 停止所有抓取器。")
        
        try:
            # 保持主线程运行
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n正在停止所有抓取器...")
            launcher.stop_all_scrapers()
            logger.info("所有抓取器已停止。")
            
    except Exception as e:
        logger.error(f"启动器运行失败: {e}")

if __name__ == "__main__":
    main() 