import datetime
import time

# Dates and timestamps
fetched_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

def timestamp_to_date(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp else None

def date_to_timestamp(date_str):
    if not date_str:
        return None
    try:
        return int(datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').timestamp())
    except ValueError:
        return None
    
print(f"fetched_at: {fetched_at}")
print(f"timestamp_to_date: {timestamp_to_date(1700000000)}")
print(f"date_to_timestamp: {date_to_timestamp('2023-11-14 12:00:00')}")