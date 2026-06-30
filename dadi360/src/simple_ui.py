#!/usr/bin/env python3
"""
简单的UI示例
展示如何使用启动器管理抓取器
为将来的Web UI做准备
"""

import os
import sys
import time
import json
from typing import Dict, Any
from loguru import logger

# 添加当前目录到路径
sys.path.append(os.path.dirname(__file__))

from scraper_launcher import ScraperLauncher

class SimpleUI:
    """简单的UI界面"""
    
    def __init__(self):
        """初始化UI"""
        self.launcher = ScraperLauncher()
        self.setup_scrapers()
    
    def setup_scrapers(self):
        """设置抓取器"""
        # 注册抓取器
        try:
            from nail.nail_refactored import NailJobScraper
            self.launcher.register_scraper("nail_jobs", NailJobScraper, "nail_jobs")
            print("✅ 美甲招聘抓取器注册成功")
        except ImportError:
            print("⚠️ 美甲招聘抓取器未找到")
        
        try:
            from rental.rental_refactored import RentalScraper
            self.launcher.register_scraper("rental", RentalScraper, "rental")
            print("✅ 租房抓取器注册成功")
        except ImportError:
            print("⚠️ 租房抓取器未找到")
        
        try:
            from restaurant.restaurant_refactored import RestaurantJobScraper
            self.launcher.register_scraper("restaurant_jobs", RestaurantJobScraper, "restaurant_jobs")
            print("✅ 餐厅招聘抓取器注册成功")
        except ImportError:
            print("⚠️ 餐厅招聘抓取器未找到")
    
    def show_menu(self):
        """显示主菜单"""
        print("\n" + "="*60)
        print("🔍 招聘信息监控系统")
        print("="*60)
        print("1. 查看抓取器状态")
        print("2. 启动抓取器")
        print("3. 停止抓取器")
        print("4. 运行一次抓取")
        print("5. 查看配置")
        print("6. 修改配置")
        print("7. 查看日志")
        print("0. 退出")
        print("="*60)
    
    def show_status(self):
        """显示抓取器状态"""
        print("\n📊 抓取器状态:")
        print("-" * 40)
        
        status = self.launcher.get_scraper_status()
        if not status:
            print("❌ 没有可用的抓取器")
            return
        
        for name, state in status.items():
            icon = "🟢" if state == "运行中" else "🔴"
            print(f"{icon} {name}: {state}")
    
    def start_scraper(self):
        """启动抓取器"""
        available_scrapers = self.launcher.list_available_scrapers()
        if not available_scrapers:
            print("❌ 没有可用的抓取器")
            return
        
        print("\n🚀 启动抓取器:")
        print("-" * 40)
        for i, name in enumerate(available_scrapers, 1):
            print(f"{i}. {name}")
        print("0. 返回")
        
        try:
            choice = input("\n请选择要启动的抓取器 (输入数字): ").strip()
            if choice == "0":
                return
            
            choice = int(choice)
            if 1 <= choice <= len(available_scrapers):
                scraper_name = available_scrapers[choice - 1]
                if self.launcher.start_scraper(scraper_name):
                    print(f"✅ {scraper_name} 启动成功")
                else:
                    print(f"❌ {scraper_name} 启动失败")
            else:
                print("❌ 无效选择")
        except ValueError:
            print("❌ 请输入有效数字")
        except KeyboardInterrupt:
            print("\n操作已取消")
    
    def stop_scraper(self):
        """停止抓取器"""
        running_scrapers = [name for name, status in self.launcher.get_scraper_status().items() 
                           if status == "运行中"]
        
        if not running_scrapers:
            print("❌ 没有正在运行的抓取器")
            return
        
        print("\n🛑 停止抓取器:")
        print("-" * 40)
        for i, name in enumerate(running_scrapers, 1):
            print(f"{i}. {name}")
        print("0. 返回")
        
        try:
            choice = input("\n请选择要停止的抓取器 (输入数字): ").strip()
            if choice == "0":
                return
            
            choice = int(choice)
            if 1 <= choice <= len(running_scrapers):
                scraper_name = running_scrapers[choice - 1]
                if self.launcher.stop_scraper(scraper_name):
                    print(f"✅ {scraper_name} 已停止")
                else:
                    print(f"❌ {scraper_name} 停止失败")
            else:
                print("❌ 无效选择")
        except ValueError:
            print("❌ 请输入有效数字")
        except KeyboardInterrupt:
            print("\n操作已取消")
    
    def run_once(self):
        """运行一次抓取"""
        available_scrapers = self.launcher.list_available_scrapers()
        if not available_scrapers:
            print("❌ 没有可用的抓取器")
            return
        
        print("\n⚡ 单次运行抓取器:")
        print("-" * 40)
        for i, name in enumerate(available_scrapers, 1):
            print(f"{i}. {name}")
        print("0. 返回")
        
        try:
            choice = input("\n请选择要运行的抓取器 (输入数字): ").strip()
            if choice == "0":
                return
            
            choice = int(choice)
            if 1 <= choice <= len(available_scrapers):
                scraper_name = available_scrapers[choice - 1]
                print(f"🔄 正在运行 {scraper_name}...")
                if self.launcher.start_scraper(scraper_name, run_once=True):
                    print(f"✅ {scraper_name} 运行完成")
                else:
                    print(f"❌ {scraper_name} 运行失败")
            else:
                print("❌ 无效选择")
        except ValueError:
            print("❌ 请输入有效数字")
        except KeyboardInterrupt:
            print("\n操作已取消")
    
    def show_config(self):
        """显示配置"""
        print("\n⚙️ 当前配置:")
        print("-" * 40)
        
        config = self.launcher.config
        
        # 显示邮箱配置
        print("📧 邮箱配置:")
        email_config = config.get("EMAIL", {})
        print(f"  发件人: {email_config.get('SENDER_EMAIL', '未设置')}")
        print(f"  收件人: {email_config.get('RECEIVER_EMAIL', '未设置')}")
        print(f"  SMTP服务器: {email_config.get('SMTP_SERVER', '未设置')}")
        print(f"  SMTP端口: {email_config.get('SMTP_PORT', '未设置')}")
        
        # 显示各抓取器配置
        print("\n🔍 抓取器配置:")
        for key, value in config.items():
            if key not in ["EMAIL", "HEADERS"] and isinstance(value, dict):
                print(f"  {key}:")
                if "keywords" in value:
                    keywords = value["keywords"][:5]  # 只显示前5个关键词
                    print(f"    关键词: {', '.join(keywords)}...")
                if "send_interval_seconds" in value:
                    hours = value["send_interval_seconds"] // 3600
                    print(f"    检查间隔: {hours} 小时")
    
    def modify_config(self):
        """修改配置"""
        print("\n⚠️ 配置修改功能正在开发中...")
        print("请直接编辑 config.json 文件")
    
    def show_logs(self):
        """查看日志"""
        print("\n📋 日志查看:")
        print("-" * 40)
        print("1. 美甲招聘日志")
        print("2. 租房监控日志")
        print("3. 餐厅招聘日志")
        print("4. 所有日志")
        print("0. 返回")
        
        try:
            choice = input("\n请选择要查看的日志: ").strip()
            if choice == "0":
                return
            
            choice = int(choice)
            if choice == 1:
                os.system("python ../view_logs.py")
            elif choice == 2:
                os.system("python ../view_logs.py")
            elif choice == 3:
                os.system("python ../view_logs.py")
            elif choice == 4:
                os.system("python ../view_logs.py")
            else:
                print("❌ 无效选择")
        except ValueError:
            print("❌ 请输入有效数字")
        except KeyboardInterrupt:
            print("\n操作已取消")
    
    def run(self):
        """运行UI"""
        print("🎉 欢迎使用招聘信息监控系统！")
        
        while True:
            try:
                self.show_menu()
                choice = input("\n请选择操作 (0-7): ").strip()
                
                if choice == "0":
                    print("👋 再见！")
                    break
                elif choice == "1":
                    self.show_status()
                elif choice == "2":
                    self.start_scraper()
                elif choice == "3":
                    self.stop_scraper()
                elif choice == "4":
                    self.run_once()
                elif choice == "5":
                    self.show_config()
                elif choice == "6":
                    self.modify_config()
                elif choice == "7":
                    self.show_logs()
                else:
                    print("❌ 无效选择，请输入 0-7")
                
                input("\n按回车键继续...")
                
            except KeyboardInterrupt:
                print("\n\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 发生错误: {e}")
                input("\n按回车键继续...")

def main():
    """主函数"""
    try:
        ui = SimpleUI()
        ui.run()
    except Exception as e:
        logger.error(f"UI运行失败: {e}")

if __name__ == "__main__":
    main() 