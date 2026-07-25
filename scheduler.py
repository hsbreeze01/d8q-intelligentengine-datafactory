"""任务调度器 - 根据freq字段和run_at时间定时执行创作和发布任务"""
import fcntl
import glob
import json
import logging
import os
import random
import sys
import threading
import time
from datetime import datetime, timedelta

# 预警扫描
# _alert_scan_last_run replaced by file-based dedup


logger = logging.getLogger(__name__)
# 确保调度器日志输出到文件
_fh = logging.FileHandler("/var/log/d8q/scheduler.log")
_fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(_fh)
logger.setLevel(logging.INFO)

TASKS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "content_tasks.json")
EXEC_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "exec_log.json")
LOCK_PATH = "/tmp/d8q_scheduler.lock"

_RUN_MARKER_DIR = "/tmp/d8q_scheduler_markers"
os.makedirs(_RUN_MARKER_DIR, exist_ok=True)

def _already_ran_today(task_name):
    """File-based dedup: prevents same task running twice across multiple workers."""
    from datetime import datetime
    marker = os.path.join(_RUN_MARKER_DIR, f"{task_name}_{datetime.now().strftime('%Y-%m-%d')}")
    if os.path.exists(marker):
        return True
    # Create marker
    with open(marker, 'w') as f:
        f.write(datetime.now().isoformat())
    # Clean old markers (>2 days)
    import glob
    for old in glob.glob(os.path.join(_RUN_MARKER_DIR, f"{task_name}_*")):
        if old != marker:
            try:
                os.remove(old)
            except:
                pass
    return False


# 热度聚合脚本路径
sys.path.insert(0, "/home/ecs-assist-user/d8q-data-agent/scripts")

# 各任务类型的默认执行时间 (HH:MM)
DEFAULT_RUN_AT = {"creation": "08:30", "publish": "08:50"}

# 每日随机偏移（防止固定时间规律被检测为自动化）
_daily_offsets = {"_date": None, "creation": 0, "publish": 0}

def _get_daily_offsets():
    """每天生成一次随机偏移量，creation 在 -5~+40 分钟，publish 在 creation+5~+50 分钟"""
    global _daily_offsets
    today = datetime.now().strftime("%Y-%m-%d")
    if _daily_offsets["_date"] != today:
        creation_offset = random.randint(-5, 40)   # 08:25 ~ 09:10
        publish_offset = random.randint(max(creation_offset + 5, -5), 50)  # 确保 publish > creation, 08:25 ~ 09:40
        _daily_offsets = {"_date": today, "creation": creation_offset, "publish": publish_offset}
        logger.info("每日随机偏移: creation=%+dmin, publish=%+dmin", creation_offset, publish_offset)
    return _daily_offsets


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
            today_creation = [entry for entry in logs if entry.get("type") == "creation"
                              and entry.get("subject") == task_subject
                              and entry.get("time", "").startswith(today)]
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



def _run_alert_scan():
    """每30分钟执行一次预警扫描"""
    # file-based dedup
    now = datetime.now()
    # 每30分钟执行一次
    current_slot = now.strftime("%Y-%m-%d %H:") + ("00" if now.minute < 30 else "30")
    if _already_ran_today(f"alert_scan_{current_slot}"):
        return

    try:
        from alert_scanner import scan_all_alerts
        logger.info("执行预警扫描任务")
        scan_all_alerts()
    except Exception as e:
        logger.error("预警扫描任务失败: %s", e)



# 自选股每日评分计算
_score_calc_last_run = ""

def daily_score_calculation():
    """每日评分计算：遍历所有用户自选股，调用SHARK获取评分并存入score_history"""
    global _score_calc_last_run
    today = datetime.now().strftime("%Y-%m-%d")
    if _score_calc_last_run == today:
        return
    now = datetime.now()
    if now.hour != 8 or now.minute < 30 or now.minute > 35:
        return
    _score_calc_last_run = today

    import urllib.request
    import urllib.parse
    import sqlite3

    SHARK_API = "http://49.234.48.221:5000"
    DB_PATH = "/home/ecs-assist-user/d8q-data-agent/data/financial_news.db"

    logger.info("开始每日自选股评分计算")

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        stocks = conn.execute("SELECT DISTINCT stock_code, stock_name FROM user_watchlist").fetchall()
        conn.close()
    except Exception as e:
        logger.error("评分计算: 获取自选股列表失败: %s", e)
        return

    calculated = 0
    failed = 0

    for row in stocks:
        code, name = row["stock_code"], row["stock_name"]
        try:
            url = SHARK_API + "/api/analysis/stock/comprehensive"
            body_bytes = json.dumps({"stock_code": code}).encode()
            req = urllib.request.Request(url, data=body_bytes, method="POST")
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())

            total_score = data.get("score")
            if total_score is not None:
                short_signal = (data.get("short_term") or {}).get("signal", "")
                mid_signal = (data.get("mid_term") or {}).get("signal", "")
                long_signal = (data.get("long_term") or {}).get("signal", "")
                signal = short_signal or mid_signal or long_signal
                conn = sqlite3.connect(DB_PATH)
                conn.execute(
                    "INSERT OR REPLACE INTO score_history (stock_code, stock_name, date, total_score, technical_score, trend_score, fundamental_score, volume_score, signal, risk_level) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (code, name or data.get("stock_name", code), today, total_score, None,
                     None, None, None, signal, data.get("risk_level"))
                )
                conn.commit()
                conn.close()
                calculated += 1
                logger.info("评分计算: %s(%s) total_score=%.1f", code, name, total_score)
            else:
                failed += 1
                logger.warning("评分计算: %s 无 score, data=%s", code, str(data)[:200])
        except Exception as e:
            failed += 1
            logger.error("评分计算: %s 失败: %s", code, e)

    logger.info("每日评分计算完成: calculated=%d, failed=%d", calculated, failed)



# === 缠论每日扫描+推送 ===
# _chanlun_scan_last_run replaced by file-based _already_ran_today

def _run_chanlun_scan():
    """每日15:35执行：触发compass缠论扫描 -> 高分信号推送企微"""
    import urllib.request
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    if _already_ran_today("chanlun_scan"):
        return
    # 工作日 15:35 触发（A股收盘后5分钟）
    if now.weekday() > 4:  # 周末跳过
        return
    if now.hour != 15 or now.minute < 35 or now.minute > 40:
        return
    logger.info("开始缠论每日扫描任务")

    # Step 1: 触发compass扫描
    try:
        req = urllib.request.Request("http://127.0.0.1:8087/chanlun/scan", method="POST",
                                    data=b"{}", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            scan_result = json.loads(resp.read())
        logger.info("缠论扫描完成: %s", scan_result)
    except Exception as e:
        logger.error("缠论扫描失败: %s", e)
        return

    # Step 2: 获取高分信号
    try:
        req = urllib.request.Request("http://127.0.0.1:8087/chanlun/signals?min_score=70&date=" + today)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        signals = data.get("signals", [])
        if not signals:
            logger.info("缠论扫描无高分信号，跳过推送")
            return
    except Exception as e:
        logger.error("获取缠论信号失败: %s", e)
        return

    # Step 3: 构建markdown并推送企微
    type_map = {"buy1": "一买", "buy2": "二买", "buy3": "三买", "sell1": "一卖", "sell2": "二卖", "sell3": "三卖"}
    lines = ["## \U0001f4d0 缠论信号 (%s)" % today, ""]
    for s in signals[:10]:  # 最多推送10个
        tn = type_map.get(s.get("signal_type", ""), s.get("signal_type", ""))
        rr = s.get("risk_reward", "-")
        lines.append("**%s** | %s | 评分<font color=\"warning\">%s</font> | 盈亏比1:%s" % (
            s.get("stock_code", ""), tn, s.get("score", ""), rr))
        lines.append("> 信号价:%s 止损:%s 目标:%s" % (
            s.get("signal_price", ""), s.get("stop_loss", ""), s.get("target_price", "")))
        lines.append("")
    lines.append("共 %d 个信号(评分≥70)" % len(signals))
    md_content = "\n".join(lines)

    try:
        req = urllib.request.Request("http://127.0.0.1:8088/api/chanlun/notify",
                                    data=json.dumps({"content": md_content, "msgtype": "markdown"}).encode("utf-8"),
                                    method="POST", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            push_result = json.loads(resp.read())
        logger.info("缠论信号推送结果: %s", push_result)
    except Exception as e:
        logger.error("缠论信号推送失败: %s", e)



# === 纪律化策略扫描（独立入口）===
# _disciplined_scan_last_run replaced by file-based _already_ran_today

def _run_disciplined_scan():
    """每日15:37执行：纪律化策略独立扫描+推送（晚于原chanlun_scan 2分钟）"""
    import subprocess
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    if _already_ran_today("disciplined_scan"):
        return
    if now.weekday() > 4:
        return
    if now.hour != 15 or now.minute < 37 or now.minute > 42:
        return
    logger.info("开始纪律化策略扫描任务")
    try:
        result = subprocess.run(
            ["/home/ecs-assist-user/d8q-intelligentengine-stockcompass/venv/bin/python3.12",
             "/home/ecs-assist-user/d8q-intelligentengine-stockcompass/chanlun/strategy/disciplined_scan.py"],
            capture_output=True, text=True, timeout=120,
            cwd="/home/ecs-assist-user/d8q-intelligentengine-stockcompass"
        )
        if result.returncode == 0:
            logger.info("纪律化策略扫描完成")
        else:
            logger.error("纪律化策略扫描失败: %s", result.stderr[:300])
    except Exception as e:
        logger.error("纪律化策略扫描异常: %s", e)



# _czsc_scan_last_run replaced by file-based _already_ran_today

def _run_czsc_scan():
    """每日15:40执行：czsc新引擎扫描(灰度，与旧引擎并行)"""
    from datetime import datetime
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    if _already_ran_today("czsc_scan"):
        return
    # 工作日 15:40 触发
    if now.weekday() >= 5:
        return
    if now.hour != 15 or now.minute < 40 or now.minute > 45:
        return
    import subprocess
    try:
        logger.info("czsc扫描开始...")
        result = subprocess.run(
            ["/home/ecs-assist-user/d8q-intelligentengine-stockcompass/venv/bin/python",
             "/home/ecs-assist-user/d8q-intelligentengine-stockcompass/chanlun/strategy/czsc_scan.py", "--push"],
            capture_output=True, text=True, timeout=300
        )
        logger.info("czsc扫描完成: %s", result.stdout.strip())
        if result.returncode != 0:
            logger.error("czsc扫描异常: %s", result.stderr[:500])
    except Exception as e:
        logger.error("czsc扫描异常: %s", e)



# === 信号复盘回填(16:00) ===
def _run_signal_review():
    """每日16:00执行：回填已产出信号的后续走势结果"""
    from datetime import datetime
    now = datetime.now()
    if now.weekday() >= 5:
        return
    if now.hour != 16 or now.minute > 5:
        return
    if _already_ran_today("signal_review"):
        return
    import subprocess
    try:
        logger.info("信号复盘开始...")
        result = subprocess.run(
            ["/home/ecs-assist-user/d8q-intelligentengine-stockcompass/venv/bin/python3.12",
             "/home/ecs-assist-user/d8q-intelligentengine-stockcompass/chanlun/strategy/signal_review.py"],
            capture_output=True, text=True, timeout=60
        )
        logger.info("信号复盘完成: %s", result.stdout.strip())
        if result.returncode != 0:
            logger.error("信号复盘异常: %s", result.stderr[:300])
    except Exception as e:
        logger.error("信号复盘异常: %s", e)



# === 周五复盘周报(16:30) ===
def _run_weekly_review():
    """每周五16:30执行：生成周报+参数建议+推送"""
    from datetime import datetime
    now = datetime.now()
    if now.weekday() != 4:  # 只在周五执行
        return
    if now.hour != 16 or now.minute < 30 or now.minute > 35:
        return
    if _already_ran_today("weekly_review"):
        return
    import subprocess
    try:
        logger.info("周报生成开始...")
        result = subprocess.run(
            ["/home/ecs-assist-user/d8q-intelligentengine-stockcompass/venv/bin/python3.12",
             "/home/ecs-assist-user/d8q-intelligentengine-stockcompass/chanlun/strategy/weekly_review.py",
             "--push"],
            capture_output=True, text=True, timeout=60
        )
        logger.info("周报完成: %s", result.stdout.strip()[:200])
    except Exception as e:
        logger.error("周报异常: %s", e)


# === 实验组扫描(15:42, 与default并行) ===
def _run_experimental_scan():
    """每日15:42执行：experimental profile灰度扫描"""
    from datetime import datetime
    now = datetime.now()
    if now.weekday() >= 5:
        return
    if now.hour != 15 or now.minute < 42 or now.minute > 47:
        return
    if _already_ran_today("experimental_scan"):
        return
    import subprocess
    try:
        logger.info("实验组扫描开始...")
        result = subprocess.run(
            ["/home/ecs-assist-user/d8q-intelligentengine-stockcompass/venv/bin/python3.12",
             "/home/ecs-assist-user/d8q-intelligentengine-stockcompass/chanlun/strategy/czsc_scan.py",
             "--profile", "experimental"],
            capture_output=True, text=True, timeout=300
        )
        logger.info("实验组扫描完成: %s", result.stdout.strip()[:200])
    except Exception as e:
        logger.error("实验组扫描异常: %s", e)

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

        # 预警扫描(每30分钟)
        _run_alert_scan()

        # 缠论每日扫描(15:35)
        _run_chanlun_scan()

        # 纪律化策略扫描(15:37, 独立入口)
        _run_disciplined_scan()

        # czsc新引擎扫描(15:40, 灰度并行)
        _run_czsc_scan()

        # 信号复盘回填(16:00)
        _run_signal_review()

        # 周五复盘周报(16:30)
        _run_weekly_review()

        # 实验组灰度扫描(15:42)
        _run_experimental_scan()

        # 每日自选股评分计算(08:30)
        daily_score_calculation()

        # 先轮询已投递的 publish 队列任务
        _poll_pending()

        # 先执行creation，再执行publish（加每日随机偏移）
        offsets = _get_daily_offsets()
        for task_type in ("creation", "publish"):
            for task in tasks:
                if task.get("type") != task_type:
                    continue
                run_h, run_m = _parse_run_at(task)
                # 应用每日随机偏移
                offset_min = offsets.get(task_type, 0)
                base_time = datetime(now.year, now.month, now.day, run_h, run_m)
                adjusted_time = base_time + timedelta(minutes=offset_min)
                adj_h, adj_m = adjusted_time.hour, adjusted_time.minute
                if now.hour != adj_h or now.minute < adj_m:
                    continue
                if not _should_run(task):
                    continue
                logger.info("调度执行: %s %s(%s) run_at=%02d:%02d offset=%+dmin adjusted=%02d:%02d",
                            task.get("id"), task_type, task.get("subject"), run_h, run_m, offset_min, adj_h, adj_m)
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
