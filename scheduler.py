import schedule
import time
import pytz
from datetime import datetime
from main import run_pipeline
from config import UPLOAD_TIMES, TIMEZONE

def check_time_and_run():
    ist_now = datetime.now(pytz.timezone(TIMEZONE))
    current_hhmm = ist_now.strftime("%H:%M")
    
    if current_hhmm in UPLOAD_TIMES:
        print(f"[{ist_now}] Triggering Automated Tamil Infotainment Pipeline for {current_hhmm} slot...")
        run_pipeline()
        time.sleep(61)  # Sleep to avoid double triggering within the same minute

def start_scheduler():
    print(f"⏰ Tamil Infotainment Scheduler Started.")
    print(f"   Target upload times: {', '.join(UPLOAD_TIMES)} (TimeZone: {TIMEZONE})")
    
    # We check every 30 seconds to ensure we hit the 1 minute window precisely
    schedule.every(30).seconds.do(check_time_and_run)
    
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"⚠️ Scheduler warning: {e}")
        time.sleep(1)

if __name__ == "__main__":
    start_scheduler()
