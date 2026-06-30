import threading
import time
from typing import Callable

class Scheduler:
    def __init__(self):
        self.jobs = []
        self.running = False

    def every(self, interval_seconds: int, job_func: Callable, *args, **kwargs):
        """添加一个定时任务，每隔interval_seconds执行一次job_func"""
        self.jobs.append({
            'interval': interval_seconds,
            'job_func': job_func,
            'args': args,
            'kwargs': kwargs,
            'next_run': time.time() + interval_seconds
        })

    def run_pending(self):
        now = time.time()
        for job in self.jobs:
            if now >= job['next_run']:
                try:
                    job['job_func'](*job['args'], **job['kwargs'])
                except Exception as e:
                    # 这里不能使用logger，因为scheduler_util是独立的工具类
                    # 错误会通过调用方的logger记录
                    pass
                job['next_run'] = now + job['interval']

    def start(self):
        self.running = True
        def loop():
            while self.running:
                self.run_pending()
                time.sleep(1)
        t = threading.Thread(target=loop, daemon=True)
        t.start()
        return t

    def stop(self):
        self.running = False 