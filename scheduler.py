"""任务调度器 - 根据freq字段定时执行创作和发布任务"""
import json
import logging
import os
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)

TASKS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "content_tasks.json")

# 频率 -> 执行间隔(秒)
FREQ_INTERVAL = {
    "daily": 24 * 3600,
    "weekly": 7 * 24 * 3600,
}

# 每日执行时间(小时)
RUN_HOUR = 8


def _load_tasks():
    try:
        with open(TASKS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_tasks(tasks):
    with open(TASKS_PATH, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def _should_run(task):
    """判断任务是否应该执行"""
    if task.get("status") == "paused":
        return False
    freq = task.get("freq", "daily")
    last_run = task.get("last_run", "")
    now = datetime.now()

    if freq == "daily":
        return last_run[:10] != now.strftime("%Y-%m-%d")
    elif freq == "weekly":
        if not last_run:
            return True
        from datetime import timedelta
        try:
            last_dt = datetime.strptime(last_run[:10], "%Y-%m-%d")
            return (now - last_dt).days >= 7
        except Exception:
            return True
    return False


def _run_task(task):
    """执行单个任务"""
    import urllib.request
    task_id = task.get("id", "")
    try:
        url = f"http://127.0.0.1:8088/api/content/tasks/{task_id}/run"
        req = urllib.request.Request(url, method="POST", data=b"{}")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read())
        logger.info("任务 %s(%s/%s) 执行完成: %s", task_id, task.get("type"), task.get("subject"), result)
        return result
    except Exception as e:
        logger.error("任务 %s 执行失败: %s", task_id, e)
        return {"error": str(e)}


def _tick():
    """一次调度检查"""
    now = datetime.now()
    if now.hour != RUN_HOUR:
        return

    tasks = _load_tasks()
    changed = False
    # 先执行creation，再执行publish（保证有内容可发布）
    for task_type in ("creation", "publish"):
        for task in tasks:
            if task.get("type") != task_type:
                continue
            if not _should_run(task):
                continue
            logger.info("调度执行: %s %s(%s)", task.get("id"), task_type, task.get("subject"))
            _run_task(task)
            task["last_run"] = now.strftime("%Y-%m-%d %H:%M:%S")
            changed = True

    if changed:
        _save_tasks(tasks)


def start_scheduler():
    """启动后台调度线程"""
    def _loop():
        logger.info("调度器已启动，每日 %d:00 执行任务", RUN_HOUR)
        while True:
            try:
                _tick()
            except Exception as e:
                logger.error("调度器异常: %s", e)
            time.sleep(300)  # 每5分钟检查一次

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return t
