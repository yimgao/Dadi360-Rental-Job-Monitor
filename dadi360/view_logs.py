#!/usr/bin/env python3
"""
日志查看工具
用于查看美甲招聘和租房监控的日志文件
"""

import os
import sys
from datetime import datetime

def print_log_content(log_file, title, max_lines=50):
    """打印日志文件内容"""
    if not os.path.exists(log_file):
        print(f"❌ {title} 文件不存在: {log_file}")
        return
    
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"📁 文件路径: {log_file}")
    print(f"📅 最后修改: {datetime.fromtimestamp(os.path.getmtime(log_file)).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        if not lines:
            print("📝 日志文件为空")
            return
            
        # 显示最后几行
        recent_lines = lines[-max_lines:] if len(lines) > max_lines else lines
        print(f"📊 显示最后 {len(recent_lines)} 行 (共 {len(lines)} 行):\n")
        
        for line in recent_lines:
            print(line.rstrip())
            
    except Exception as e:
        print(f"❌ 读取日志文件失败: {e}")

def main():
    print("🔍 日志查看工具")
    print("="*60)
    
    # 检查日志目录是否存在
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        print(f"❌ 日志目录不存在: {logs_dir}")
        print("请先运行监控脚本生成日志文件")
        return
    
    # 美甲招聘日志
    print_log_content("logs/nail_jobs_info.log", "美甲招聘 - 信息日志")
    print_log_content("logs/nail_jobs_error.log", "美甲招聘 - 错误日志")
    
    # 租房日志
    print_log_content("logs/rental_info.log", "租房监控 - 信息日志")
    print_log_content("logs/rental_error.log", "租房监控 - 错误日志")
    
    # 餐厅招聘日志
    print_log_content("logs/restaurant_jobs_info.log", "餐厅招聘 - 信息日志")
    print_log_content("logs/restaurant_jobs_error.log", "餐厅招聘 - 错误日志")
    
    print(f"\n{'='*60}")
    print("✅ 日志查看完成")
    print("💡 提示:")
    print("   • 信息日志包含所有运行信息、成功操作和警告")
    print("   • 错误日志只包含错误和严重问题")
    print("   • 日志文件会自动轮转和清理")
    print("   • 可以随时运行此脚本查看最新日志")
    print("   • 所有日志文件都保存在项目根目录的 logs/ 文件夹中")

if __name__ == "__main__":
    main() 