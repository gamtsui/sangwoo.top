"""
自动化调度器 - 定时任务入口
通过 FastAPI BackgroundTasks 或独立 cron 进程运行

Cron 配置:
- 新闻爬虫: 每日 08:00
- 备份: 每日 02:00
- 健康监控: 每 5 分钟
"""
import asyncio
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ============ 调度配置 ============
SCHEDULES = [
    {
        "name": "news_pipeline",
        "cron": "0 8 * * *",       # Daily at 08:00
        "func": "_run_news_pipeline",
    },
    {
        "name": "backup",
        "cron": "0 2 * * *",       # Daily at 02:00
        "func": "_run_backup",
    },
    {
        "name": "health_check",
        "interval_seconds": 300,    # Every 5 minutes
        "func": "_run_health_check",
    },
]


def _run_news_pipeline():
    """Run the news crawl -> rewrite -> publish pipeline."""
    from .database import init_db
    from .models import SystemLog
    from .publish import publish_articles

    init_db()
    session_func = lambda: __import__('contextlib').contextmanager(lambda: ().__class__)

    async def _run():
        stats = await publish_articles(max_articles=10, days_back=7)
        return stats

    try:
        stats = asyncio.run(_run())
        logger.info(f"News pipeline: {stats}")
        return stats
    except Exception as e:
        logger.error(f"News pipeline failed: {e}")
        return {"error": str(e)}


def _run_backup():
    """Run the S3 backup."""
    from .backup import run_backup
    try:
        result = run_backup()
        logger.info(f"Backup: {result['status']}")
        return result
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return {"status": "failed", "error": str(e)}


def _run_health_check():
    """Run health monitoring."""
    from .health_monitor import run_health_check
    try:
        status = run_health_check()
        if status["overall"] != "healthy":
            logger.warning(f"Health check: {status['overall']}")
        return status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"overall": "error", "error": str(e)}


# ============ Simple Scheduler ============
class SimpleScheduler:
    """Lightweight scheduler for cron-like tasks."""

    def __init__(self, schedules: list[dict] | None = None):
        self.schedules = schedules or SCHEDULES
        self._running = False
        self._tasks = []

    def start(self):
        """Start the scheduler (blocks)."""
        self._running = True
        logger.info("Scheduler started")

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

        # Start async event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        for sched in self.schedules:
            task = loop.create_task(self._schedule_task(sched))
            self._tasks.append(task)

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        """Stop the scheduler."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        logger.info("Scheduler stopped")

    def _handle_shutdown(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()

    async def _schedule_task(self, sched: dict):
        """Run a single scheduled task."""
        name = sched["name"]
        func_ref = sched["func"]

        # Resolve function
        func = getattr(self, func_ref, None)
        if not func:
            logger.error(f"Function not found: {func_ref}")
            return

        if "cron" in sched:
            await self._cron_loop(name, func, sched["cron"])
        elif "interval_seconds" in sched:
            await self._interval_loop(name, func, sched["interval_seconds"])

    async def _cron_loop(self, name: str, func, cron_expr: str):
        """Run task on cron schedule."""
        while self._running:
            next_run = self._next_cron_time(cron_expr)
            now = datetime.now()
            delay = (next_run - now).total_seconds()

            if delay > 0:
                logger.info(f"[{name}] Next run in {delay:.0f}s ({next_run.strftime('%H:%M:%S')})")
                await asyncio.sleep(delay)
            else:
                await asyncio.sleep(60)  # Safety: at least 1 min between runs

            if not self._running:
                break

            logger.info(f"[{name}] Running...")
            try:
                result = func()
                logger.info(f"[{name}] Completed: {result}")
            except Exception as e:
                logger.error(f"[{name}] Failed: {e}")

    async def _interval_loop(self, name: str, func, interval: int):
        """Run task at fixed interval."""
        while self._running:
            logger.info(f"[{name}] Running...")
            try:
                result = func()
                logger.info(f"[{name}] Completed")
            except Exception as e:
                logger.error(f"[{name}] Failed: {e}")

            await asyncio.sleep(interval)

    @staticmethod
    def _next_cron_time(cron_expr: str) -> datetime:
        """Calculate next cron execution time (simplified: only supports 'M H * * *')."""
        parts = cron_expr.split()
        if len(parts) != 5:
            raise ValueError(f"Unsupported cron expression: {cron_expr}")

        minute = int(parts[0])
        hour = int(parts[1])

        now = datetime.now()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if next_run <= now:
            next_run += timedelta(days=1)

        return next_run


# ============ Standalone Runner ============
def run_scheduler():
    """Run the scheduler as a standalone process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(message)s',
    )

    scheduler = SimpleScheduler()
    scheduler.start()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sangwoo automation scheduler")
    parser.add_argument("--task", choices=["news", "backup", "health", "all"],
                       default="all", help="Task to run")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    if args.once:
        if args.task == "news":
            result = _run_news_pipeline()
        elif args.task == "backup":
            result = _run_backup()
        elif args.task == "health":
            result = _run_health_check()
        else:
            results = {
                "news": _run_news_pipeline(),
                "backup": _run_backup(),
                "health": _run_health_check(),
            }
            result = results
        print(json.dumps(result, indent=2, default=str))
    else:
        run_scheduler()
