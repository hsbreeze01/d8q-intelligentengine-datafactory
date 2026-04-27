"""任务调度器 - 根据freq字段和run_at时间定时执行创作和发布任务"""
import json
import logging
import os
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)

TASKS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "content_tasks.json")

# 各任务类型的默认执行时间 (HH:MM)
DEFAULT_RUN_AT = {"creation": "08:30", "publish": "08:50"}


def _load_tasks():
    try:
        with open(TASKS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_tasks(tasks):
    with open(TASKS_PATH, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def _parse_run_at(task):
    """解析任务的 run_at 字段，返回 (hour, minute)"""
    run_at = task.get("run_at") or DEFAULT_RUN_AT.get(task.get("type", ""), "08:00")
    try:
        h, m = run_at.split(":")
        return int(h), int(m)
    except Exception:
        return 8, 0


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
        url = f"http://127.0.0.1:8088/api/content/tasks/{task_id}/run?trigger=scheduler"
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
    tasks = _load_tasks()
    changed = False

    # 先执行creation，再执行publish
    for task_type in ("creation", "publish"):
        for task in tasks:
            if task.get("type") != task_type:
                continue
            run_h, run_m = _parse_run_at(task)
            if now.hour != run_h or now.minute < run_m:
                continue
            if not _should_run(task):
                continue
            logger.info("调度执行: %s %s(%s) run_at=%02d:%02d",
                        task.get("id"), task_type, task.get("subject"), run_h, run_m)
            _run_task(task)
            task["last_run"] = now.strftime("%Y-%m-%d %H:%M:%S")
            changed = True

    if changed:
        _save_tasks(tasks)


def start_scheduler():
    """启动后台调度线程"""
    def _loop():
        logger.info("调度器已启动，执行时间由各任务 run_at 字段控制")
        while True:
            try:
                _tick()
            except Exception as e:
                logger.error("调度器异常: %s", e)
            time.sleep(60)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return t
