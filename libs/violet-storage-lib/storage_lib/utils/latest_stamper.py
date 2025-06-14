import datetime
import json
from io import BytesIO

class LatestStamper:
    """
    A class to manage the latest timestamp for a given key.
    """

    def __init__(
            self,
            utc_time: datetime.datetime = datetime.datetime.now(datetime.UTC)
        ) -> None:
        self._utc_time = utc_time


    @property
    def now(self) -> datetime.datetime:
        """
        Returns the current datetime in UTC.
        """
        return self._utc_time
    
    @property
    def today(self) -> str:
        """
        Returns the current date in 'YYYY-MM-DD' format.
        """
        return self._utc_time.strftime("%Y-%m-%d")

    @property
    def json_bytes_io(
            self
        ) -> BytesIO:
        """
        Returns the latest metadata as a BytesIO object.
        """
        today = self.today
        today_iso_str = self._utc_time.isoformat()
        timestamp = int(datetime.datetime.fromisoformat(today_iso_str).timestamp())
        date_str = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        json_data = {
            "date": today,
            "ISO_date": today_iso_str,
            "timestamp": timestamp,
            "date_str": date_str
        }

        return BytesIO(json.dumps(json_data).encode('utf-8'))