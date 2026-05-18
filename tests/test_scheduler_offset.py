"""Tests for scheduler _get_daily_offsets() and offset application in _tick()"""
import importlib
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import patch


# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reload_scheduler():
    """Reload the scheduler module to reset module-level _daily_offsets state."""
    import scheduler
    importlib.reload(scheduler)
    return scheduler


# ---------------------------------------------------------------------------
# 1. Creation offset range: [-5, +40]
# ---------------------------------------------------------------------------

class TestCreationOffsetRange:
    def test_creation_offset_within_range(self):
        """creation offset should always be between -5 and +40 minutes."""
        sched = _reload_scheduler()
        for _ in range(200):
            # Reset cached date so a new offset is generated each iteration
            sched._daily_offsets = {"_date": None, "creation": 0, "publish": 0}
            offsets = sched._get_daily_offsets()
            assert -5 <= offsets["creation"] <= 40, (
                f"creation offset {offsets['creation']} outside [-5, 40]"
            )


# ---------------------------------------------------------------------------
# 2. Publish offset > creation offset invariant
# ---------------------------------------------------------------------------

class TestPublishGreaterThanCreation:
    def test_publish_offset_greater_than_creation(self):
        """publish offset must always be >= creation offset + 5."""
        sched = _reload_scheduler()
        for _ in range(200):
            sched._daily_offsets = {"_date": None, "creation": 0, "publish": 0}
            offsets = sched._get_daily_offsets()
            assert offsets["publish"] >= offsets["creation"] + 5, (
                f"publish {offsets['publish']} not >= creation {offsets['creation']} + 5"
            )
            # publish upper bound is 50
            assert offsets["publish"] <= 50

    def test_publish_offset_range(self):
        """publish offset should fall within [-5, 50]."""
        sched = _reload_scheduler()
        for _ in range(200):
            sched._daily_offsets = {"_date": None, "creation": 0, "publish": 0}
            offsets = sched._get_daily_offsets()
            assert -5 <= offsets["publish"] <= 50


# ---------------------------------------------------------------------------
# 3. Same-day stability
# ---------------------------------------------------------------------------

class TestSameDayStability:
    def test_offset_stable_within_same_day(self):
        """Calling _get_daily_offsets() multiple times on the same day returns
        identical values."""
        sched = _reload_scheduler()
        today_str = datetime.now().strftime("%Y-%m-%d")
        # First call generates
        first = sched._get_daily_offsets()
        assert first["_date"] == today_str
        # Subsequent calls must return same values
        for _ in range(10):
            again = sched._get_daily_offsets()
            assert again["creation"] == first["creation"]
            assert again["publish"] == first["publish"]
            assert again["_date"] == today_str


# ---------------------------------------------------------------------------
# 4. Daily regeneration
# ---------------------------------------------------------------------------

class TestDailyRegeneration:
    def test_new_date_regenerates_offsets(self):
        """When the date changes, new offsets should be generated."""
        sched = _reload_scheduler()
        # Force-set to yesterday
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        sched._daily_offsets = {"_date": yesterday, "creation": -99, "publish": -99}
        offsets = sched._get_daily_offsets()
        today_str = datetime.now().strftime("%Y-%m-%d")
        assert offsets["_date"] == today_str
        assert offsets["creation"] != -99
        assert offsets["publish"] != -99
        assert -5 <= offsets["creation"] <= 40

    def test_regenerates_when_date_changes(self):
        """Simulate date rollover: set _date to yesterday, verify new offsets."""
        sched = _reload_scheduler()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        # Seed with a known stale date and sentinel values
        sched._daily_offsets = {"_date": yesterday, "creation": -99, "publish": -90}

        offsets = sched._get_daily_offsets()
        today_str = datetime.now().strftime("%Y-%m-%d")
        assert offsets["_date"] == today_str
        # Values must have been regenerated from the sentinel values
        assert offsets["creation"] != -99
        assert offsets["publish"] != -90
        assert -5 <= offsets["creation"] <= 40
        assert offsets["publish"] >= offsets["creation"] + 5


# ---------------------------------------------------------------------------
# 5. Offset application in _tick() time comparison logic
# ---------------------------------------------------------------------------

class TestTickOffsetApplication:
    """Test that _tick() correctly applies offsets when deciding whether to run
    a task. We patch the module-level references after import."""

    def _make_scheduler(self):
        sched = _reload_scheduler()
        return sched

    def test_tick_applies_positive_offset(self):
        """With a +20 min offset on a task with run_at=08:30, _tick should
        only execute when current time >= 08:50."""
        sched = self._make_scheduler()

        frozen_0845 = datetime(2025, 6, 1, 8, 45)
        frozen_0851 = datetime(2025, 6, 1, 8, 51)

        offsets_val = {
            "_date": "2025-06-01",
            "creation": 20,
            "publish": 25,
        }

        task = {
            "id": "t1",
            "type": "creation",
            "subject": "test",
            "run_at": "08:30",
            "status": "active",
            "freq": "daily",
            "last_run": "",
        }

        with patch.object(sched, "datetime", wraps=sys.modules["scheduler"].datetime) as mock_dt, \
             patch.object(sched, "_get_daily_offsets", return_value=offsets_val), \
             patch.object(sched, "_load_tasks", return_value=[dict(task)]), \
             patch.object(sched, "_run_task", return_value={"ok": True}) as mock_run, \
             patch.object(sched, "_save_tasks"), \
             patch.object(sched, "_poll_pending"), \
             patch.object(sched, "_run_daily_extras"):
            # We can't easily mock datetime.now for the module-level import,
            # so we use a different approach: patch datetime directly in the module
            pass

        # Alternative: directly test the time comparison logic extracted
        # by verifying the behavior through _tick with full module patching
        sched2 = self._make_scheduler()

        with patch("scheduler.datetime") as mock_dt, \
             patch("scheduler._get_daily_offsets", return_value=offsets_val), \
             patch("scheduler._load_tasks", return_value=[dict(task)]), \
             patch("scheduler._run_task", return_value={"ok": True}) as mock_run, \
             patch("scheduler._save_tasks"), \
             patch("scheduler._poll_pending"), \
             patch("scheduler._run_daily_extras"):

            # Make datetime(2025,6,1,...) constructors work
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            mock_dt.now.return_value = frozen_0845
            # timedelta is imported from datetime module, also used in _tick
            # but since we only patch "scheduler.datetime", timedelta still works

            sched2._tick()

            # Should NOT have run — 08:45 < adjusted 08:50
            mock_run.assert_not_called()

            # Advance to 08:51
            mock_dt.now.return_value = frozen_0851
            task["last_run"] = ""
            sched2._daily_offsets = offsets_val

            sched2._tick()
            mock_run.assert_called_once()

    def test_tick_negative_offset_runs_earlier(self):
        """With a -5 min offset on a task with run_at=08:30, _tick should
        execute at 08:25."""
        sched = self._make_scheduler()

        frozen_now = datetime(2025, 6, 1, 8, 25)

        offsets_val = {
            "_date": "2025-06-01",
            "creation": -5,
            "publish": 5,
        }

        task = {
            "id": "t2",
            "type": "creation",
            "subject": "early",
            "run_at": "08:30",
            "status": "active",
            "freq": "daily",
            "last_run": "",
        }

        with patch("scheduler.datetime") as mock_dt, \
             patch("scheduler._get_daily_offsets", return_value=offsets_val), \
             patch("scheduler._load_tasks", return_value=[dict(task)]), \
             patch("scheduler._run_task", return_value={"ok": True}) as mock_run, \
             patch("scheduler._save_tasks"), \
             patch("scheduler._poll_pending"), \
             patch("scheduler._run_daily_extras"):

            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            mock_dt.now.return_value = frozen_now

            sched._tick()

            # Should have run — adjusted time is 08:25, now is 08:25
            mock_run.assert_called_once()
