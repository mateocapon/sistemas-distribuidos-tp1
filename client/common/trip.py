import datetime


class Trip:
    def __init__(self, start_date: str, start_station_code: str, end_date: str,
                 end_station_code: str, duration_sec: str, is_member: str, yearid: str):
        self.start_date = start_date
        self.start_station_code = start_station_code
        self.end_date = end_date
        self.end_station_code = end_station_code
        self.duration_sec = duration_sec
        self.is_member = is_member
        self.yearid = yearid

