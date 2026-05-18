"""任务调度器 - 根据freq字段和run_at时间定时执行创作和发布任务"""
import fcntl
import json
import logging
import os
import sys
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)
# 确保调度器日志输出到文件
_fh = logging.FileHandler("/var/log/d8q/scheduler.log")
_fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(_fh)
logger.setLevel(logging.INFO)

TASKS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "content_tasks.json")
EXEC_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "exec_log.json")
LOCK_PATH = "/tmp/d8q_scheduler.lock"

# 热度聚合脚本路径
sys.path.insert(0, "/home/ecs-assist-user/d8q-data-agent/scripts")

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
    task_type = task.get("type", "")
    task_subject = task.get("subject", "")

    # publish 任务：检查今日 creation 是否成功，失败则跳过
    if task_type == "publish":
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            with open(EXEC_LOG_PATH, encoding="utf-8") as f:
                import json as _j
                logs = _j.load(f)
            # 查找今日同 subject 的 creation 记录
            today_creation = [l for l in logs if l.get("type") == "creation"
                              and l.get("subject") == task_subject
                              and l.get("time", "").startswith(today)]
            if today_creation and not today_creation[0].get("success", False):
                logger.info("跳过 publish %s: 今日 creation 失败 (%s)", task_subject, today_creation[0].get("result_summary", ""))
                return {"error": "skipped_creation_failed", "subject": task_subject, "reason": "今日创作任务失败，跳过发布"}
        except Exception:
            pass  # 无 exec_log 则不阻断

        # publish 前检查 infopublisher 健康状态
        try:
            health_req = urllib.request.Request("http://127.0.0.1:8089/api/health")
            with urllib.request.urlopen(health_req, timeout=5) as h_resp:
                h_data = json.loads(h_resp.read())
                if h_data.get("status") != "ok":
                    logger.warning("infopublisher 健康检查异常: %s，跳过发布", h_data)
                    return {"error": "publisher_unhealthy", "subject": task_subject}
        except Exception as he:
            logger.error("infopublisher 不可达: %s，跳过发布", he)
            return {"error": "publisher_unreachable", "subject": task_subject, "reason": str(he)[:200]}

    # 按 task 类型设置超时：creation 300s (LLM 生成), publish 15s (队列投递，不再等待完成)
    timeout = 15 if task_type == "publish" else 300

    try:
        url = f"http://127.0.0.1:8088/api/content/tasks/{task_id}/run?trigger=scheduler"
        req = urllib.request.Request(url, method="POST", data=b"{}")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read())
        logger.info("任务 %s(%s/%s) 执行完成: %s", task_id, task_type, task_subject, result)
        # publish 任务：解析队列返回，保存 queue_task_id 和 queue_status
        if task_type == "publish" and result.get("task_id") and result.get("status") in ("queued", "running"):
            task["queue_task_id"] = result["task_id"]
            task["queue_status"] = result["status"]
            logger.info("publish %s 已投递队列 queue_task_id=%s", task_subject, result["task_id"])
        return result
    except urllib.error.HTTPError as e:
        err_body = e.read()
        try:
            err_result = json.loads(err_body)
        except Exception:
            err_result = {"error": f"HTTP {e.code}: {err_body[:200]}"}
        logger.error("任务 %s 执行失败 (HTTP %d): %s", task_id, e.code, err_result)
        return err_result
    except Exception as e:
        logger.error("任务 %s 执行失败: %s", task_id, e)
        return {"error": str(e)}


def _poll_pending():
    """轮询已投递的 publish 队列任务，检查完成状态"""
    import urllib.request
    tasks = _load_tasks()
    changed = False
    for task in tasks:
        if task.get("queue_status") not in ("queued", "running"):
            continue
        queue_task_id = task.get("queue_task_id", "")
        if not queue_task_id:
            continue
        try:
            url = f"http://127.0.0.1:8089/api/publish/queue/{queue_task_id}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
            status = result.get("status", "")
            if status in ("completed", "failed"):
                task["queue_status"] = status
                changed = True
                success = status == "completed"
                _append_scheduler_exec_log(task, result, success, trigger=task.get("queue_trigger", "scheduler"))
                logger.info("publish %s 队列完成: status=%s", task.get("subject", ""), status)
            # queued/running → 等待下次轮询
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # queue_task_id 在 publisher 侧丢失（重启后队列清空），标记为 lost
                task["queue_status"] = "lost"
                changed = True
                logger.warning("publish %s 队列任务丢失(queue_task_id=%s)，标记为 lost", task.get("subject", ""), queue_task_id)
            else:
                logger.warning("poll publish queue %s HTTP错误: %s", queue_task_id, e)
        except Exception as e:
            logger.warning("poll publish queue %s 失败: %s", queue_task_id, e)
    if changed:
        _save_tasks(tasks)


def _append_scheduler_exec_log(task, result, success, trigger="scheduler"):
    """scheduler 轮询完成后写入 exec_log，格式与手动触发一致"""
    import fcntl
    entry = {
        "task_id": task.get("id", ""),
        "type": task.get("type", ""),
        "subject": task.get("subject", ""),
        "trigger": trigger,
        "success": success,
        "result_summary": result.get("error") or result.get("title") or result.get("status") or str(result)[:100],
        "duration": 0,
        "time": datetime.now().isoformat(),
    }
    try:
        with open(EXEC_LOG_PATH, "r+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            logs = json.load(f)
            logs.insert(0, entry)
            logs = logs[:200]
            f.seek(0)
            f.truncate()
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(EXEC_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump([entry], f, ensure_ascii=False, indent=2)


# --- 每日附加任务的执行状态 ---
_daily_extras_last_run = ""


def _run_daily_extras():
    """每日 07:00 执行：热度聚合 → 热度异动检测 + 政策分析"""
    global _daily_extras_last_run
    today = datetime.now().strftime("%Y-%m-%d")
    if _daily_extras_last_run == today:
        return
    now = datetime.now()
    if now.hour != 7 or now.minute > 5:
        return
    _daily_extras_last_run = today
    try:
        # 1. 先聚合热度（确保今日 track_heat_daily 有数据）
        from heat_aggregator import aggregate_today
        heat_result = aggregate_today(days=1)
        logger.info("热度聚合结果: %d 条, %s", len(heat_result), heat_result)
    except Exception as e:
        logger.error("热度聚合失败: %s", e)
    try:
        # 2. 热度异动检测 + 政策分析（依赖步骤1的数据）
        from heat_anomaly import detect_heat_anomaly, run_policy_analysis, run_investment_collection
        logger.info("执行每日附加任务: 热度异动检测 + 政策分析")
        r1 = detect_heat_anomaly()
        logger.info("热度异动检测结果: %s", r1)
        r2 = run_policy_analysis()
        r3 = run_investment_collection()
        logger.info("投融资采集结果: %s", r3)
        logger.info("政策分析结果: %s", r2)
    except Exception as e:
        logger.error("每日附加任务失败: %s", e)


def _tick():
    """一次调度检查（带文件锁防止多worker重复执行）"""
    lock_fd = open(LOCK_PATH, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_fd.close()
        return

    try:
        now = datetime.now()
        tasks = _load_tasks()
        changed = False

        # 每日附加任务
        _run_daily_extras()

        # 先轮询已投递的 publish 队列任务
        _poll_pending()

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
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()


def start_scheduler():
    """启动后台调度线程"""
    def _loop():
        logger.info("调度器已启动 (pid=%d)，执行时间由各任务 run_at 字段控制", os.getpid())
        while True:
            try:
                _tick()
            except Exception as e:
                logger.error("调度器异常: %s", e)
            time.sleep(60)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return t
