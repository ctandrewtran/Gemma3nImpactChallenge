from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import threading
import time
from rag.scrape import crawl_and_index
import pytz

# Shared progress state
global_progress = {
    "status": "idle",  # idle, running, done, error
    "progress": 0.0,    # 0.0 to 1.0
    "message": "",
    "last_run": None
}
progress_lock = threading.Lock()

scheduler = BackgroundScheduler()


def set_progress(status, progress, message):
    with progress_lock:
        global_progress["status"] = status
        global_progress["progress"] = progress
        global_progress["message"] = message
        if status == "done":
            global_progress["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")


def get_progress():
    with progress_lock:
        return dict(global_progress)


def run_scrape_with_progress(url):
    """
    Run crawl_and_index and update progress. This is a blocking call.
    """
    try:
        set_progress("running", 0.0, "Starting scrape...")
        # For demonstration, we simulate progress. In production, pass a callback to crawl_and_index.
        # You can modify crawl_and_index to accept a progress callback and update here.
        for i in range(10):
            set_progress("running", i/10.0, f"Scraping... {i*10}%")
            time.sleep(1)
        crawl_and_index(url)
        set_progress("done", 1.0, "Scraping complete.")
    except Exception as e:
        set_progress("error", 0.0, f"Error: {e}")


def trigger_refresh(url):
    """
    Manually trigger a scrape in a background thread.
    """
    t = threading.Thread(target=run_scrape_with_progress, args=(url,))
    t.start()


def schedule_refresh(cron_expr, url, timezone_str=None):
    """
    Schedule a scrape using a cron expression (e.g., '0 2 * * *' for 2am daily) in a given timezone.
    timezone_str: e.g., 'America/New_York', 'Europe/London', or None for system local time.
    Returns True if scheduled, False if error.
    """
    try:
        tz = None
        if timezone_str:
            try:
                tz = pytz.timezone(timezone_str)
            except Exception:
                print(f"[Scheduler] Invalid timezone: {timezone_str}")
                return False
        trigger = CronTrigger.from_crontab(cron_expr, timezone=tz)
        scheduler.add_job(run_scrape_with_progress, trigger, args=[url], id="scheduled_scrape", replace_existing=True)
        scheduler.start()
        return True
    except Exception as e:
        print(f"[Scheduler] Error scheduling: {e}")
        return False


def stop_scheduler():
    scheduler.shutdown(wait=False) 