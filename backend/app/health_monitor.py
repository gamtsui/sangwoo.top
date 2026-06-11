"""
系统健康监控 - 监控 CPU/内存/磁盘/服务进程
阈值: CPU>80% 持续 5min、内存>85%、磁盘>90%
自动处理: 内存趋势增长→优雅重启 FastAPI；服务无响应→重启容器
"""
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Optional

import psutil

logger = logging.getLogger(__name__)

# ============ 阈值配置 ============
THRESHOLDS = {
    "cpu_warning": 80,      # CPU > 80% 持续 5min 告警
    "memory_warning": 85,   # 内存 > 85% 告警
    "disk_warning": 90,     # 磁盘 > 90% 告警
    "cpu_critical": 95,     # CPU > 95% 立即告警
    "memory_critical": 95,  # 内存 > 95% 立即告警
    "disk_critical": 95,    # 磁盘 > 95% 立即告警
}

# 持续监控时间窗口 (秒)
SUSTAINED_WINDOW = 300  # 5 minutes

# 监控的检查项
SERVICES_TO_CHECK = ["uvicorn", "nginx"]


class HealthMonitor:
    def __init__(self, thresholds: dict | None = None):
        self.thresholds = thresholds or THRESHOLDS
        self._cpu_history = []  # (timestamp, cpu_percent)
        self._alerts_sent = set()  # Track alerts sent in this session

    def check_all(self) -> dict:
        """Run all health checks, return status dict."""
        cpu = self._check_cpu()
        memory = self._check_memory()
        disk = self._check_disk()
        services = self._check_services()
        docker = self._check_docker()

        status = {
            "timestamp": datetime.now().isoformat(),
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "services": services,
            "docker": docker,
            "overall": "healthy",
        }

        # Determine overall status
        checks = [cpu, memory, disk, services, docker]
        if any(c.get("status") == "critical" for c in checks):
            status["overall"] = "critical"
        elif any(c.get("status") == "warning" for c in checks):
            status["overall"] = "warning"

        return status

    def _check_cpu(self) -> dict:
        """Check CPU usage with sustained monitoring."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0

            self._cpu_history.append((time.time(), cpu_percent))
            # Keep only last 5 minutes
            cutoff = time.time() - SUSTAINED_WINDOW
            self._cpu_history = [(t, v) for t, v in self._cpu_history if t > cutoff]

            # Check sustained high CPU
            sustained_high = False
            if len(self._cpu_history) >= 60:  # At least 60 data points
                recent = [v for _, v in self._cpu_history[-60:]]
                avg_recent = sum(recent) / len(recent)
                if avg_recent > self.thresholds["cpu_warning"]:
                    sustained_high = True

            status = "healthy"
            actions = []
            if cpu_percent > self.thresholds["cpu_critical"]:
                status = "critical"
                actions.append("CPU critically high - check running processes")
            elif cpu_percent > self.thresholds["cpu_warning"] or sustained_high:
                status = "warning"
                if sustained_high:
                    actions.append("CPU sustained high (>80% for 5min)")

            return {
                "status": status,
                "percent": cpu_percent,
                "cores": cpu_count,
                "load_avg": load_avg,
                "sustained_high": sustained_high,
                "actions": actions,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _check_memory(self) -> dict:
        """Check memory usage."""
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            status = "healthy"
            actions = []

            if mem.percent > self.thresholds["memory_critical"]:
                status = "critical"
                actions.append("Memory critically high - consider graceful restart")
            elif mem.percent > self.thresholds["memory_warning"]:
                status = "warning"
                actions.append("Memory high - monitoring for growth trend")

            # Top memory consumers
            top_procs = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    top_procs.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "memory_percent": round(proc.info['memory_percent'], 1),
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            top_procs.sort(key=lambda x: x['memory_percent'], reverse=True)

            return {
                "status": status,
                "percent": mem.percent,
                "total_gb": round(mem.total / (1024**3), 1),
                "available_gb": round(mem.available / (1024**3), 1),
                "used_gb": round(mem.used / (1024**3), 1),
                "swap_percent": swap.percent,
                "top_processes": top_procs[:5],
                "actions": actions,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _check_disk(self) -> dict:
        """Check disk usage."""
        try:
            disk = psutil.disk_usage('/')
            data_disk = None
            if os.path.exists('/data'):
                try:
                    data_disk = psutil.disk_usage('/data')
                except:
                    pass

            status = "healthy"
            actions = []

            if disk.percent > self.thresholds["disk_critical"]:
                status = "critical"
                actions.append("Disk critically high - clean old backups/logs")
            elif disk.percent > self.thresholds["disk_warning"]:
                status = "warning"
                actions.append("Disk usage high - consider cleanup")

            result = {
                "status": status,
                "root": {
                    "total_gb": round(disk.total / (1024**3), 1),
                    "used_gb": round(disk.used / (1024**3), 1),
                    "free_gb": round(disk.free / (1024**3), 1),
                    "percent": disk.percent,
                },
                "actions": actions,
            }

            if data_disk:
                result["data"] = {
                    "total_gb": round(data_disk.total / (1024**3), 1),
                    "used_gb": round(data_disk.used / (1024**3), 1),
                    "free_gb": round(data_disk.free / (1024**3), 1),
                    "percent": data_disk.percent,
                }

            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _check_services(self) -> dict:
        """Check if required services are running."""
        services = {}
        for service in SERVICES_TO_CHECK:
            running = False
            pids = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info.get('cmdline', []) or [])
                    if service in cmdline or service in (proc.info.get('name') or ''):
                        running = True
                        pids.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            services[service] = {
                "running": running,
                "pids": pids[:3],  # Show first 3 PIDs
            }

        all_running = all(s["running"] for s in services.values())
        return {
            "status": "healthy" if all_running else "warning",
            "services": services,
            "actions": [] if all_running else ["Some services not running"],
        }

    def _check_docker(self) -> dict:
        """Check Docker containers status."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}\\t{{.Status}}"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return {"status": "error", "error": "Docker not accessible"}

            containers = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('\t')
                    name = parts[0] if parts else ""
                    status = parts[1] if len(parts) > 1 else ""
                    containers.append({"name": name, "status": status})

            all_healthy = all(
                "Up" in c["status"] for c in containers
            )

            return {
                "status": "healthy" if all_healthy else "warning",
                "containers": containers,
                "actions": [] if all_healthy else ["Some containers not healthy"],
            }
        except FileNotFoundError:
            return {"status": "error", "error": "Docker CLI not found"}
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "Docker check timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def auto_remediation(self, status: dict) -> list[str]:
        """Execute automatic remediation actions based on status."""
        actions_taken = []

        # Memory critically high - suggest graceful restart
        if status.get("memory", {}).get("status") == "critical":
            logger.warning("Memory critical - signaling graceful FastAPI restart")
            try:
                # Send SIGHUP to uvicorn for graceful reload
                for proc in psutil.process_iter(['pid', 'cmdline']):
                    try:
                        cmdline = ' '.join(proc.info.get('cmdline', []) or [])
                        if 'uvicorn' in cmdline and 'sangwoo' in cmdline:
                            os.kill(proc.info['pid'], signal.SIGHUP)
                            actions_taken.append(f"Sent SIGHUP to uvicorn PID {proc.info['pid']}")
                    except (psutil.NoSuchProcess, ProcessLookupError, PermissionError):
                        pass
            except Exception as e:
                actions_taken.append(f"Failed to restart: {e}")

        # Disk critically high - clean old logs
        if status.get("disk", {}).get("status") == "critical":
            try:
                import glob
                log_files = glob.glob('/data/logs/*.log.*')
                log_files.sort()
                cleaned = 0
                for f in log_files[:-5]:  # Keep last 5 rotated logs
                    try:
                        os.remove(f)
                        cleaned += 1
                    except:
                        pass
                actions_taken.append(f"Cleaned {cleaned} old log files")
            except Exception as e:
                actions_taken.append(f"Failed to clean logs: {e}")

        return actions_taken


def run_health_check() -> dict:
    """Convenience function: run health check and return result."""
    monitor = HealthMonitor()
    status = monitor.check_all()

    if status["overall"] != "healthy":
        actions = monitor.auto_remediation(status)
        status["remediation"] = actions

    return status


if __name__ == "__main__":
    import json
    import signal

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')

    status = run_health_check()
    print(json.dumps(status, indent=2))
    sys.exit(0 if status["overall"] == "healthy" else 1)
